"""Market data operations for Hyperliquid API."""

from typing import Any, Dict, Optional

from hyperliquid_mcp.clients.base_client import BaseHyperliquidClient
from hyperliquid_mcp.logging_config import get_logger

logger = get_logger(__name__)


class MarketClient(BaseHyperliquidClient):
    """Client for market data operations using Hyperliquid Info API."""

    # Market Data Methods
    async def get_funding_rates(
        self,
        asset: Optional[str] = None,
        include_history: bool = False,
        start_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get current and historical funding rates from fundingHistory + metaAndAssetCtxs endpoints.

        Args:
            asset: Asset symbol to filter by (optional)
            include_history: Whether to include historical funding data
            start_time: Start time for historical data (required if include_history=True)

        Returns:
            Enhanced funding rates data
        """
        result: dict = {"current_funding": {}, "historical_funding": {}}

        # Get current funding from meta and contexts
        meta_and_contexts = self.info.meta_and_asset_ctxs()
        if len(meta_and_contexts) >= 2:
            universe = meta_and_contexts[0].get("universe", [])
            asset_contexts = meta_and_contexts[1]

            for i, ctx in enumerate(asset_contexts):
                if i < len(universe) and isinstance(ctx, dict):
                    asset_name = universe[i].get("name", "")
                    if not asset or asset_name == asset:
                        result["current_funding"][asset_name] = ctx

        # Get historical funding if requested
        if include_history and asset and start_time:
            historical = self.info.funding_history(asset, start_time)
            for h in historical:
                h.pop("coin", None)

            result["historical_funding"][asset] = historical

        return result

    async def get_market_data(self, asset: str) -> Dict[str, Any]:
        """
        Get detailed market data for a specific asset from metaAndAssetCtxs endpoint.

        Args:
            asset: Asset symbol

        Returns:
            Rich market data for the specific asset including price, funding, volume, etc.
        """
        meta_and_contexts = self.info.meta_and_asset_ctxs()

        if len(meta_and_contexts) < 2:
            raise ValueError("Insufficient data from metaAndAssetCtxs endpoint")

        universe = meta_and_contexts[0].get("universe", [])
        asset_contexts = meta_and_contexts[1]

        # Find the asset in the universe
        asset_index = None
        asset_info = None
        for i, meta in enumerate(universe):
            if meta.get("name") == asset:
                asset_index = i
                asset_info = meta
                break

        if asset_info is None:
            raise ValueError(f"Asset {asset} not found in universe")

        if asset_contexts and asset_index and asset_index >= len(asset_contexts):
            raise ValueError(f"No context data available for {asset}")

        ctx = asset_contexts[asset_index]

        return asset_info | ctx

    async def get_candle_data(
        self, asset: str, interval: str, start_time: int, end_time: int
    ) -> Dict[str, Any]:
        """
        Get historical candle/OHLCV data from candleSnapshot endpoint.

        Args:
            asset: Asset symbol
            interval: Time interval (1m, 5m, 1h, 1d, etc.)
            start_time: Start time in epoch milliseconds
            end_time: End time in epoch milliseconds

        Returns:
            Enhanced candle data
        """
        raw_candles = self.info.candles_snapshot(asset, interval, start_time, end_time)

        # Enhance candle data for easier consumption
        def safe_float(value, default="0"):
            """Safely convert a value to float, handling None and empty values."""
            if value is None or value == "":
                return float(default)
            try:
                return float(value)
            except (ValueError, TypeError):
                return float(default)

        enhanced_candles = []
        for candle in raw_candles:
            if isinstance(candle, dict) and "t" in candle:
                enhanced_candle = {
                    "timestamp": candle.get("t", 0),
                    "open": safe_float(candle.get("o")),
                    "high": safe_float(candle.get("h")),
                    "low": safe_float(candle.get("l")),
                    "close": safe_float(candle.get("c")),
                    "volume": safe_float(candle.get("v")),
                    "number_of_trades": candle.get("n", 0),
                }
                enhanced_candles.append(enhanced_candle)

        # Calculate some basic statistics
        if enhanced_candles:
            prices = [c["close"] for c in enhanced_candles]
            volumes = [c["volume"] for c in enhanced_candles]

            stats = {
                "total_candles": len(enhanced_candles),
                "price_range": {
                    "min": min(prices),
                    "max": max(prices),
                    "first": enhanced_candles[0]["open"],
                    "last": enhanced_candles[-1]["close"],
                },
                "volume_stats": {
                    "total": sum(volumes),
                    "average": sum(volumes) / len(volumes),
                    "max": max(volumes),
                },
            }
        else:
            stats = {"total_candles": 0}

        return {
            "asset": asset,
            "interval": interval,
            "time_range": {"start_time": start_time, "end_time": end_time},
            "candles": enhanced_candles,
            "statistics": stats,
        }

    async def get_l2_orderbook(
        self, asset: str, significant_figures: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get L2 order book depth from l2Book endpoint.

        Args:
            asset: Asset symbol
            significant_figures: Number of significant figures for price aggregation (optional)

        Returns:
            Enhanced L2 orderbook data
        """
        raw_orderbook = self.info.l2_snapshot(asset)

        if not raw_orderbook or "levels" not in raw_orderbook:
            return {
                "asset": asset,
                "bids": [],
                "asks": [],
                "spread": 0,
                "error": "No orderbook data available",
            }

        levels = raw_orderbook.get("levels", [])
        bids = []
        asks = []

        # Helper function for safe float conversion
        def safe_float(value, default="0"):
            """Safely convert a value to float, handling None and empty values."""
            if value is None or value == "":
                return float(default)
            try:
                return float(value)
            except (ValueError, TypeError):
                return float(default)

        # Handle new format where levels is an array of two arrays: [bids_array, asks_array]
        if (
            len(levels) == 2
            and isinstance(levels[0], list)
            and isinstance(levels[1], list)
        ):
            # New format: levels[0] = bids, levels[1] = asks
            bid_levels = levels[0]
            ask_levels = levels[1]

            # Process bids
            for level in bid_levels:
                if isinstance(level, dict) and "px" in level and "sz" in level:
                    price = safe_float(level["px"])
                    size = safe_float(level["sz"])
                    n_orders = level.get("n", 0)

                    level_data = {
                        "price": price,
                        "size": size,
                        "value": price * size,
                        "n_orders": n_orders,
                    }
                    bids.append(level_data)

            # Process asks
            for level in ask_levels:
                if isinstance(level, dict) and "px" in level and "sz" in level:
                    price = safe_float(level["px"])
                    size = safe_float(level["sz"])
                    n_orders = level.get("n", 0)

                    level_data = {
                        "price": price,
                        "size": size,
                        "value": price * size,
                        "n_orders": n_orders,
                    }
                    asks.append(level_data)
        else:
            # Legacy format: levels is a flat array with side indicators
            for level in levels:
                if isinstance(level, dict) and "px" in level and "sz" in level:
                    price = safe_float(level["px"])
                    size = safe_float(level["sz"])
                    side = level.get("side", "")
                    n_orders = level.get("n", 0)

                    level_data = {
                        "price": price,
                        "size": size,
                        "value": price * size,
                        "n_orders": n_orders,
                    }

                    if side == "B":  # Bid
                        bids.append(level_data)
                    elif side == "A":  # Ask
                        asks.append(level_data)

        # Sort bids (highest first) and asks (lowest first)
        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])

        # Calculate spread and other metrics
        spread = 0
        mid_price = 0
        if bids and asks:
            best_bid = bids[0]["price"]
            best_ask = asks[0]["price"]
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2

        # Calculate depth metrics
        bid_depth = sum(b["value"] for b in bids)
        ask_depth = sum(a["value"] for a in asks)

        return {
            "asset": asset,
            "timestamp": raw_orderbook.get("time", 0),
            "bids": bids,
            "asks": asks,
            "market_metrics": {
                "best_bid": bids[0]["price"] if bids else 0,
                "best_ask": asks[0]["price"] if asks else 0,
                "spread": spread,
                "spread_pct": (spread / mid_price * 100) if mid_price > 0 else 0,
                "mid_price": mid_price,
                "bid_depth_usd": bid_depth,
                "ask_depth_usd": ask_depth,
                "total_depth_usd": bid_depth + ask_depth,
                "bid_levels": len(bids),
                "ask_levels": len(asks),
                "total_orders": sum(b["n_orders"] for b in bids)
                + sum(a["n_orders"] for a in asks),
            },
        }

    async def calculate_min_order_size(
        self, asset: str, min_value_usd: float = 10.0
    ) -> Dict[str, Any]:
        """
        Calculate minimum order size to meet minimum order value requirement.

        Args:
            asset: Asset symbol
            min_value_usd: Minimum order value in USD

        Returns:
            Minimum order size calculation
        """

        # Get current price with safe conversion
        def safe_float(value, default="0"):
            """Safely convert a value to float, handling None and empty values."""
            if value is None or value == "":
                return float(default)
            try:
                return float(value)
            except (ValueError, TypeError):
                return float(default)

        all_mids = self.info.all_mids()
        current_price = safe_float(all_mids.get(asset))

        if current_price <= 0:
            raise ValueError(f"Invalid price for {asset}: {current_price}")

        # Get asset metadata for decimals
        meta = self.info.meta()
        universe = meta.get("universe", [])
        asset_info = next((a for a in universe if a["name"] == asset), None)

        if not asset_info:
            raise ValueError(f"Asset {asset} not found in universe")

        sz_decimals = asset_info.get("szDecimals", 0)

        # Calculate minimum size needed with a buffer
        min_size = (min_value_usd * 1.05) / current_price  # 5% buffer
        rounded_size = round(min_size, sz_decimals)

        # Verify the value meets minimum
        estimated_value = rounded_size * current_price
        if estimated_value < min_value_usd:
            # Increase size until we meet minimum
            increment = 1 / (10**sz_decimals)  # Smallest possible increment
            while estimated_value < min_value_usd:
                rounded_size += increment
                estimated_value = rounded_size * current_price
            rounded_size = round(rounded_size, sz_decimals)

        logger.info(
            f"Calculated min order size for {asset}: {rounded_size} (price: ${current_price}, value: ${estimated_value:.2f})"
        )

        return {
            "asset": asset,
            "current_price": current_price,
            "min_value_required": min_value_usd,
            "calculated_min_size": rounded_size,
            "estimated_value": estimated_value,
            "size_decimals": sz_decimals,
            "price_buffer_pct": 5.0,
            "meets_minimum": estimated_value >= min_value_usd,
            "asset_info": asset_info,
        }
