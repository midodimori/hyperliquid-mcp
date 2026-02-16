"""HTTP transport for Hyperliquid MCP Server (Streamable HTTP)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from ..config import Config


async def run_http_server(
    mcp: FastMCP, config: Config, log_level: str = "info"
) -> None:
    """Run the MCP server over HTTP transport (Streamable HTTP).

    Args:
        mcp: FastMCP server instance.
        config: Server configuration.
        log_level: Log level (debug, info, warn, error).
    """
    host = config.transport.network.host
    port = config.transport.network.port

    print(f"Starting MCP HTTP server at http://{host}:{port}/mcp", file=sys.stderr)

    await mcp.run_async(transport="http", host=host, port=port, show_banner=False)
