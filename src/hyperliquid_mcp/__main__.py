"""Entry point for Hyperliquid MCP Server."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .config import Config
from .logging_config import get_logger, setup_logging
from .server import create_server
from .transports import run_http_server, run_sse_server, run_stdio_server


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="hyperliquid-mcp",
        description="Hyperliquid MCP Server - Trading operations via Model Context Protocol",
        epilog="""
Examples:
  # Run with stdio (default)
  hyperliquid-mcp

  # Run with HTTP transport
  hyperliquid-mcp --transport http --port 3000

  # Run with SSE transport
  hyperliquid-mcp --transport sse --port 3000
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--transport",
        "-t",
        type=str,
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=3000,
        help="Port to listen on (default: 3000)",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        choices=["debug", "info", "warn", "error"],
        default="info",
        help="Log level (default: info)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 1.0.3",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    show_logs = os.getenv("HYPERLIQUID_MCP_SHOW_LOGS", "false").lower() == "true"
    setup_logging(include_console=show_logs)

    logger = get_logger(__name__)

    # Validate environment variables
    required_vars = ["HYPERLIQUID_PRIVATE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Some trading operations may not be available")

    # Build config from CLI args
    config = Config()
    config.transport.type = args.transport
    config.transport.network.host = args.host
    config.transport.network.port = args.port

    # Create server
    mcp = create_server(config)

    logger.info("Starting Hyperliquid MCP Server...")

    # Run with appropriate transport
    async def run() -> None:
        if args.transport == "stdio":
            await run_stdio_server(mcp, config)
        elif args.transport == "http":
            await run_http_server(mcp, config, log_level=args.log_level)
        elif args.transport == "sse":
            await run_sse_server(mcp, config, log_level=args.log_level)
        else:
            print(f"Unknown transport type: {args.transport}", file=sys.stderr)
            sys.exit(1)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
