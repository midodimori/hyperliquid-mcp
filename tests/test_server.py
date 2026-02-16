"""Test suite for Hyperliquid MCP Server tools."""

from unittest.mock import patch

import pytest

from hyperliquid_mcp.config import Config
from hyperliquid_mcp.models import (
    AssetFilterRequest,
    BulkCancelRequest,
    CalculateMinOrderSizeRequest,
    CancelOrderRequest,
    CandleInterval,
    GetCandleDataRequest,
    GetFundingRatesRequest,
    GetL2OrderbookRequest,
    GetMarketDataRequest,
    GetUserFillsRequest,
    ModifyOrderRequest,
    OrderStatusRequest,
    OrderType,
    PlaceOrderRequest,
    TimeInForce,
    UpdateLeverageRequest,
    UserAddressRequest,
    WithdrawRequest,
)
from hyperliquid_mcp.server import create_server

# Valid Ethereum address for testing
TEST_ADDRESS = "0x1234567890123456789012345678901234567890"


@pytest.fixture
def mcp_server():
    """Create a fresh MCP server for each test."""
    return create_server(Config())


@pytest.fixture
def mock_clients():
    """Create mock specialized clients."""
    with (
        patch("hyperliquid_mcp.capabilities.account.AccountClient") as mock_account_cls,
        patch("hyperliquid_mcp.capabilities.market.MarketClient") as mock_market_cls,
        patch("hyperliquid_mcp.capabilities.order.OrderClient") as mock_order_cls,
    ):
        mock_account = mock_account_cls.return_value
        mock_market = mock_market_cls.return_value
        mock_order = mock_order_cls.return_value

        yield {"account": mock_account, "market": mock_market, "order": mock_order}


@pytest.fixture
def mcp_with_mocks(mock_clients):
    """Create an MCP server with mocked clients."""
    mcp = create_server(Config())
    return mcp


class TestAccountTools:
    """Test account-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_positions(self, mock_clients, mcp_with_mocks):
        """Test get_positions tool."""
        mock_clients["account"].get_positions.return_value = {
            "positions": [],
            "margin_summary": {},
        }

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_positions"].fn
        result = await tool_func(request)

        mock_clients["account"].get_positions.assert_called_once_with(TEST_ADDRESS)
        assert "positions" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_positions_error(self, mock_clients, mcp_with_mocks):
        """Test get_positions tool error handling."""
        mock_clients["account"].get_positions.side_effect = Exception("API Error")

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_positions"].fn
        result = await tool_func(request)

        assert "error" in result
        assert result["error"] == "API Error"

    @pytest.mark.asyncio
    async def test_update_leverage(self, mock_clients, mcp_with_mocks):
        """Test update_leverage tool."""
        mock_clients["account"].update_leverage.return_value = {"status": "ok"}

        request = UpdateLeverageRequest(asset="ETH", leverage=10, is_isolated=True)
        tool_func = mcp_with_mocks._tool_manager._tools["update_leverage"].fn
        result = await tool_func(request)

        mock_clients["account"].update_leverage.assert_called_once_with("ETH", 10, True)
        assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_withdraw(self, mock_clients, mcp_with_mocks):
        """Test withdraw tool."""
        mock_clients["account"].withdraw.return_value = {"status": "ok"}

        request = WithdrawRequest(destination=TEST_ADDRESS, amount=50.0)
        tool_func = mcp_with_mocks._tool_manager._tools["withdraw"].fn
        result = await tool_func(request)

        mock_clients["account"].withdraw.assert_called_once_with(TEST_ADDRESS, 50.0)
        assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_spot_user_state(self, mock_clients, mcp_with_mocks):
        """Test get_spot_user_state tool."""
        mock_clients["account"].get_spot_user_state.return_value = {"balances": []}

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_spot_user_state"].fn
        result = await tool_func(request)

        mock_clients["account"].get_spot_user_state.assert_called_once_with(
            TEST_ADDRESS
        )
        assert "balances" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_user_fees(self, mock_clients, mcp_with_mocks):
        """Test get_user_fees tool."""
        mock_clients["account"].get_user_fees.return_value = {"fees": {}}

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_user_fees"].fn
        result = await tool_func(request)

        mock_clients["account"].get_user_fees.assert_called_once_with(TEST_ADDRESS)
        assert "fees" in result or "error" in result


class TestMarketDataTools:
    """Test market data related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_market_data(self, mock_clients, mcp_with_mocks):
        """Test get_market_data tool."""
        mock_clients["market"].get_market_data.return_value = {
            "asset": "ETH",
            "current_price": 2000.0,
        }

        request = GetMarketDataRequest(asset="ETH")
        tool_func = mcp_with_mocks._tool_manager._tools["get_market_data"].fn
        result = await tool_func(request)

        mock_clients["market"].get_market_data.assert_called_once_with("ETH")
        assert "asset" in result or "error" in result

    @pytest.mark.asyncio
    async def test_calculate_min_order_size(self, mock_clients, mcp_with_mocks):
        """Test calculate_min_order_size tool."""
        mock_clients["market"].calculate_min_order_size.return_value = {
            "calculated_min_size": 0.1
        }

        request = CalculateMinOrderSizeRequest(asset="ETH", min_value_usd=10.0)
        tool_func = mcp_with_mocks._tool_manager._tools["calculate_min_order_size"].fn
        result = await tool_func(request)

        mock_clients["market"].calculate_min_order_size.assert_called_once_with(
            "ETH", 10.0
        )
        assert "calculated_min_size" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_candle_data(self, mock_clients, mcp_with_mocks):
        """Test get_candle_data tool."""
        mock_clients["market"].get_candle_data.return_value = {"candles": []}

        request = GetCandleDataRequest(
            asset="ETH",
            interval=CandleInterval.ONE_HOUR,
            start_time=1640995200000,
            end_time=1641081600000,
        )
        tool_func = mcp_with_mocks._tool_manager._tools["get_candle_data"].fn
        result = await tool_func(request)

        mock_clients["market"].get_candle_data.assert_called_once_with(
            "ETH", "1h", 1640995200000, 1641081600000
        )
        assert "candles" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_funding_rates(self, mock_clients, mcp_with_mocks):
        """Test get_funding_rates tool."""
        mock_clients["market"].get_funding_rates.return_value = {
            "current_funding": {},
            "historical_funding": {},
        }

        request = GetFundingRatesRequest(
            asset="ETH", include_history=True, start_time=1640995200000
        )
        tool_func = mcp_with_mocks._tool_manager._tools["get_funding_rates"].fn
        result = await tool_func(request)

        mock_clients["market"].get_funding_rates.assert_called_once_with(
            "ETH", True, 1640995200000
        )
        assert "current_funding" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_l2_orderbook(self, mock_clients, mcp_with_mocks):
        """Test get_l2_orderbook tool."""
        mock_clients["market"].get_l2_orderbook.return_value = {"bids": [], "asks": []}

        request = GetL2OrderbookRequest(asset="ETH", significant_figures=3)
        tool_func = mcp_with_mocks._tool_manager._tools["get_l2_orderbook"].fn
        result = await tool_func(request)

        mock_clients["market"].get_l2_orderbook.assert_called_once_with("ETH", 3)
        assert "bids" in result or "error" in result


class TestOrderManagementTools:
    """Test order management related MCP tools."""

    @pytest.mark.asyncio
    async def test_place_order(self, mock_clients, mcp_with_mocks):
        """Test place_order tool."""
        mock_clients["order"].place_order.return_value = {
            "success": True,
            "order_ids": {"main_order": [123]},
        }

        request = PlaceOrderRequest(
            asset="ETH",
            is_buy=True,
            size=1.0,
            order_type=OrderType.LIMIT,
            price=2000.0,
            time_in_force=TimeInForce.GTC,
            reduce_only=False,
        )
        tool_func = mcp_with_mocks._tool_manager._tools["place_order"].fn
        result = await tool_func(request)

        mock_clients["order"].place_order.assert_called_once_with(
            "ETH", True, 1.0, "limit", 2000.0, "GTC", False, None, None
        )
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cancel_order(self, mock_clients, mcp_with_mocks):
        """Test cancel_order tool."""
        mock_clients["order"].cancel_order.return_value = {"success": True}

        request = CancelOrderRequest(asset="ETH", order_id=123)
        tool_func = mcp_with_mocks._tool_manager._tools["cancel_order"].fn
        result = await tool_func(request)

        mock_clients["order"].cancel_order.assert_called_once_with("ETH", 123)
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_open_orders(self, mock_clients, mcp_with_mocks):
        """Test get_open_orders tool."""
        mock_clients["order"].get_open_orders.return_value = {"orders": []}

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_open_orders"].fn
        result = await tool_func(request)

        mock_clients["order"].get_open_orders.assert_called_once_with(TEST_ADDRESS)
        assert "orders" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_order_status(self, mock_clients, mcp_with_mocks):
        """Test get_order_status tool."""
        mock_clients["order"].get_order_status.return_value = {"status": "filled"}

        request = OrderStatusRequest(order_id=123, user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_order_status"].fn
        result = await tool_func(request)

        mock_clients["order"].get_order_status.assert_called_once_with(
            123, TEST_ADDRESS
        )
        assert "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_modify_order(self, mock_clients, mcp_with_mocks):
        """Test modify_order tool."""
        mock_clients["order"].modify_order.return_value = {"success": True}

        request = ModifyOrderRequest(
            asset="ETH",
            order_id=123,
            new_price=2100.0,
            new_size=1.5,
            new_time_in_force=TimeInForce.IOC,
        )
        tool_func = mcp_with_mocks._tool_manager._tools["modify_order"].fn
        result = await tool_func(request)

        mock_clients["order"].modify_order.assert_called_once_with(
            "ETH", 123, 2100.0, 1.5, "IOC"
        )
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_bulk_cancel_orders(self, mock_clients, mcp_with_mocks):
        """Test bulk_cancel_orders tool."""
        mock_clients["order"].bulk_cancel_orders.return_value = {"success": True}

        orders = [{"asset": "ETH", "order_id": 123}, {"asset": "BTC", "order_id": 456}]
        request = BulkCancelRequest(orders=orders)
        tool_func = mcp_with_mocks._tool_manager._tools["bulk_cancel_orders"].fn
        result = await tool_func(request)

        mock_clients["order"].bulk_cancel_orders.assert_called_once_with(orders)
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_cancel_all_orders(self, mock_clients, mcp_with_mocks):
        """Test cancel_all_orders tool."""
        mock_clients["order"].cancel_all_orders.return_value = {"success": True}

        request = AssetFilterRequest(asset="ETH")
        tool_func = mcp_with_mocks._tool_manager._tools["cancel_all_orders"].fn
        result = await tool_func(request)

        mock_clients["order"].cancel_all_orders.assert_called_once_with("ETH")
        assert "success" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_user_fills(self, mock_clients, mcp_with_mocks):
        """Test get_user_fills tool."""
        mock_clients["order"].get_user_fills.return_value = {"fills": []}

        request = UserAddressRequest(user=TEST_ADDRESS)
        tool_func = mcp_with_mocks._tool_manager._tools["get_user_fills"].fn
        result = await tool_func(request)

        mock_clients["order"].get_user_fills.assert_called_once_with(TEST_ADDRESS)
        assert "fills" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_user_fills_by_time(self, mock_clients, mcp_with_mocks):
        """Test get_user_fills_by_time tool."""
        mock_clients["order"].get_user_fills_by_time.return_value = {"fills": []}

        request = GetUserFillsRequest(
            start_time=1640995200000, end_time=1641081600000, user=TEST_ADDRESS
        )
        tool_func = mcp_with_mocks._tool_manager._tools["get_user_fills_by_time"].fn
        result = await tool_func(request)

        mock_clients["order"].get_user_fills_by_time.assert_called_once_with(
            1640995200000, 1641081600000, TEST_ADDRESS
        )
        assert "fills" in result or "error" in result


class TestServerStructure:
    """Test server structure and client usage."""

    def test_mcp_server_exists(self):
        """Test that MCP server is properly initialized."""
        from hyperliquid_mcp.server import mcp

        assert mcp is not None
        assert hasattr(mcp, "_tool_manager")

    def test_create_server_factory(self):
        """Test that create_server returns a configured FastMCP instance."""
        from fastmcp import FastMCP

        config = Config()
        config.server.name = "Test Server"
        server = create_server(config)

        assert isinstance(server, FastMCP)
        assert server.name == "Test Server"

    def test_all_tools_are_registered(self):
        """Test that all expected tools are properly registered."""
        mcp = create_server(Config())
        tools = list(mcp._tool_manager._tools.keys())

        expected_tools = [
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
            "get_user_fills_by_time",
        ]

        for tool in expected_tools:
            assert tool in tools, f"Tool {tool} not found in registered tools"

        assert len(tools) == len(
            expected_tools
        ), f"Expected {len(expected_tools)} tools, found {len(tools)}: {tools}"

    def test_error_handling_pattern(self, mock_clients, mcp_with_mocks):
        """Test that all tools follow the same error handling pattern."""
        mock_clients["account"].get_positions.side_effect = Exception("Test error")
        mock_clients["market"].get_market_data.side_effect = Exception("Test error")
        mock_clients["order"].get_open_orders.side_effect = Exception("Test error")

        account_request = UserAddressRequest(user=TEST_ADDRESS)
        account_tool = mcp_with_mocks._tool_manager._tools["get_positions"].fn

        market_request = GetMarketDataRequest(asset="ETH")
        market_tool = mcp_with_mocks._tool_manager._tools["get_market_data"].fn

        order_request = UserAddressRequest(user=TEST_ADDRESS)
        order_tool = mcp_with_mocks._tool_manager._tools["get_open_orders"].fn

        import asyncio

        async def test_errors():
            account_result = await account_tool(account_request)
            market_result = await market_tool(market_request)
            order_result = await order_tool(order_request)

            assert "error" in account_result
            assert "error" in market_result
            assert "error" in order_result

            assert account_result["error"] == "Test error"
            assert market_result["error"] == "Test error"
            assert order_result["error"] == "Test error"

        asyncio.run(test_errors())
