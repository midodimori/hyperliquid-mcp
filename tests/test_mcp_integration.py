"""Integration tests for MCP server functionality."""

import os
from unittest.mock import patch

from fastmcp import FastMCP

from hyperliquid_mcp.config import Config
from hyperliquid_mcp.server import create_server, mcp


class TestMCPServerIntegration:
    """Test MCP server integration and tool registration."""

    def test_mcp_server_creation(self):
        """Test that MCP server is created correctly."""
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "Hyperliquid MCP Server"

    def test_create_server_with_custom_config(self):
        """Test that create_server respects config."""
        config = Config()
        config.server.name = "Custom Server"
        server = create_server(config)

        assert isinstance(server, FastMCP)
        assert server.name == "Custom Server"

    def test_all_tools_registered(self):
        """Test that all expected tools are registered with the MCP server."""
        server = create_server(Config())
        expected_tools = {
            # Account tools
            "get_positions",
            "update_leverage",
            "withdraw",
            "get_spot_user_state",
            "get_user_fees",
            # Market data tools
            "get_market_data",
            "calculate_min_order_size",
            "get_candle_data",
            "get_user_fills_by_time",
            "get_funding_rates",
            "get_l2_orderbook",
            # Order management tools
            "place_order",
            "cancel_order",
            "get_open_orders",
            "get_order_status",
            "modify_order",
            "bulk_cancel_orders",
            "cancel_all_orders",
            "get_user_fills",
        }

        registered_tools = set(server._tool_manager._tools.keys())

        missing_tools = expected_tools - registered_tools
        extra_tools = registered_tools - expected_tools

        assert not missing_tools, f"Missing tools: {missing_tools}"
        assert not extra_tools, f"Unexpected tools: {extra_tools}"
        assert registered_tools == expected_tools

    @patch.dict(os.environ, {"HYPERLIQUID_PRIVATE_KEY": "test_key"})
    @patch("hyperliquid_mcp.__main__.create_server")
    @patch("hyperliquid_mcp.__main__.get_logger")
    def test_main_with_env_vars(self, mock_get_logger, mock_create_server):
        """Test main function with required environment variables."""
        from unittest.mock import MagicMock

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_mcp = MagicMock()
        mock_create_server.return_value = mock_mcp

        from hyperliquid_mcp.__main__ import main

        with patch("sys.argv", ["hyperliquid-mcp"]):
            # main() calls asyncio.run which would block, so just test arg parsing
            with patch("asyncio.run"):
                main()

        mock_logger.info.assert_called_with("Starting Hyperliquid MCP Server...")

    @patch.dict(os.environ, {}, clear=True)
    @patch("hyperliquid_mcp.__main__.create_server")
    @patch("hyperliquid_mcp.__main__.get_logger")
    def test_main_without_env_vars(self, mock_get_logger, mock_create_server):
        """Test main function without required environment variables."""
        from unittest.mock import MagicMock

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_mcp = MagicMock()
        mock_create_server.return_value = mock_mcp

        from hyperliquid_mcp.__main__ import main

        with patch("sys.argv", ["hyperliquid-mcp"]):
            with patch("asyncio.run"):
                main()

        mock_logger.warning.assert_any_call(
            "Missing environment variables: ['HYPERLIQUID_PRIVATE_KEY']"
        )
        mock_logger.warning.assert_any_call(
            "Some trading operations may not be available"
        )
        mock_logger.info.assert_called_with("Starting Hyperliquid MCP Server...")

    def test_tool_docstrings(self):
        """Test that all tools have proper docstrings."""
        server = create_server(Config())
        for tool_name, tool in server._tool_manager._tools.items():
            func = tool.fn
            assert func.__doc__ is not None, f"Tool {tool_name} missing docstring"
            assert (
                len(func.__doc__.strip()) > 0
            ), f"Tool {tool_name} has empty docstring"

            docstring = func.__doc__
            assert "Returns:" in docstring, f"Tool {tool_name} missing Returns section"

            import inspect

            sig = inspect.signature(func)
            if len(sig.parameters) > 0:
                assert (
                    "Args:" in docstring
                ), f"Tool {tool_name} takes parameters but missing Args section"
