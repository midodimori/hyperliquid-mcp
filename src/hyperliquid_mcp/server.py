"""Hyperliquid MCP Server implementation using fastmcp."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp import FastMCP

from hyperliquid_mcp.capabilities import (
    register_account_tools,
    register_market_tools,
    register_order_tools,
)

if TYPE_CHECKING:
    from hyperliquid_mcp.config import Config


def create_server(config: Config | None = None) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        config: Server configuration. If None, uses defaults.

    Returns:
        Configured FastMCP server instance.
    """
    if config is None:
        from hyperliquid_mcp.config import Config

        config = Config()

    server: FastMCP = FastMCP(name=config.server.name)

    # Register all tool capabilities
    register_account_tools(server)
    register_market_tools(server)
    register_order_tools(server)

    return server


# Module-level server instance for backward compatibility
mcp: FastMCP = create_server()
