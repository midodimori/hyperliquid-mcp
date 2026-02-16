"""SSE transport for Hyperliquid MCP Server."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from ..config import Config


async def run_sse_server(mcp: FastMCP, config: Config, log_level: str = "info") -> None:
    """Run the MCP server over SSE transport.

    Args:
        mcp: FastMCP server instance.
        config: Server configuration.
        log_level: Log level (debug, info, warn, error).
    """
    host = config.transport.network.host
    port = config.transport.network.port

    print(f"Starting MCP SSE server at http://{host}:{port}/sse", file=sys.stderr)

    await mcp.run_async(transport="sse", host=host, port=port, show_banner=False)
