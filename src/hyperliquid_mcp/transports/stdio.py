"""Stdio transport for Hyperliquid MCP Server."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from ..config import Config


async def run_stdio_server(mcp: FastMCP, config: Config) -> None:
    """Run the MCP server over stdio transport.

    Args:
        mcp: FastMCP server instance.
        config: Server configuration.
    """
    await mcp.run_async(show_banner=False)
