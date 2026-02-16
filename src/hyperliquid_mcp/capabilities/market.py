"""Market data tool registrations for Hyperliquid MCP Server."""

from typing import Any, Dict

from fastmcp import FastMCP

from hyperliquid_mcp.clients.market import MarketClient
from hyperliquid_mcp.logging_config import get_logger
from hyperliquid_mcp.models import (
    CalculateMinOrderSizeRequest,
    GetCandleDataRequest,
    GetFundingRatesRequest,
    GetL2OrderbookRequest,
    GetMarketDataRequest,
)

logger = get_logger(__name__)


def register_market_tools(mcp: FastMCP) -> None:
    """Register market data tools with the MCP server.

    Args:
        mcp: FastMCP server instance.
    """
    market_client = MarketClient()

    @mcp.tool()
    async def get_market_data(request: GetMarketDataRequest) -> Dict[str, Any]:
        """
        Get market data for a specific asset from Hyperliquid.

        Args:
            request: Market data request with asset symbol

        Returns:
            Market data
        """
        try:
            return await market_client.get_market_data(request.asset)
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def calculate_min_order_size(
        request: CalculateMinOrderSizeRequest,
    ) -> Dict[str, Any]:
        """
        Calculate the minimum order size needed to meet Hyperliquid's minimum order value requirement.

        Args:
            request: Min order size calculation request with asset and minimum value

        Returns:
            Minimum order size calculation
        """
        try:
            return await market_client.calculate_min_order_size(
                request.asset, request.min_value_usd
            )
        except Exception as e:
            logger.error(f"Error calculating min order size: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_candle_data(request: GetCandleDataRequest) -> Dict[str, Any]:
        """
        Get historical candle/OHLCV data for a specific asset from Hyperliquid.

        Args:
            request: Candle data request with asset, interval, and time range

        Returns:
            Historical candle data
        """
        try:
            return await market_client.get_candle_data(
                request.asset,
                request.interval.value,
                request.start_time,
                request.end_time,
            )
        except Exception as e:
            logger.error(f"Error getting candle data: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_funding_rates(request: GetFundingRatesRequest) -> Dict[str, Any]:
        """
        Get current and historical funding rates for perpetual contracts.

        Args:
            request: Funding rates request with optional asset filter and history options

        Returns:
            Funding rates data
        """
        try:
            return await market_client.get_funding_rates(
                request.asset, request.include_history, request.start_time
            )
        except Exception as e:
            logger.error(f"Error getting funding rates: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_l2_orderbook(request: GetL2OrderbookRequest) -> Dict[str, Any]:
        """
        Get L2 order book depth for a specific asset from Hyperliquid.

        Args:
            request: L2 orderbook request with asset and optional significant figures

        Returns:
            L2 orderbook data
        """
        try:
            return await market_client.get_l2_orderbook(
                request.asset, request.significant_figures
            )
        except Exception as e:
            logger.error(f"Error getting L2 orderbook: {e}")
            return {"error": str(e)}
