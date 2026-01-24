"""Order management operations for Hyperliquid API."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

from hyperliquid_mcp.logging_config import get_logger
from hyperliquid_mcp.tools.base_client import BaseHyperliquidClient

logger = get_logger(__name__)


class OrderClient(BaseHyperliquidClient):
    """Client for order management operations using Hyperliquid Info and Exchange APIs."""

    # Helper Methods
    async def get_leverage_and_decimals(self, coin: str) -> tuple[int, int]:
        """Get leverage and decimals for a coin."""
        meta = self.info.meta()
        coin_info = next((m for m in meta["universe"] if m["name"] == coin), None)
        if not coin_info:
            raise ValueError(f"Coin {coin} not found")
        return coin_info["maxLeverage"], coin_info["szDecimals"]

    async def round_to_tick_size(self, coin: str, price: float) -> float:
        """Round price to comply with Hyperliquid's price validation rules."""
        meta = self.info.meta()
        coin_info = next((m for m in meta["universe"] if m["name"] == coin), None)
        if not coin_info:
            raise ValueError(f"Coin {coin} not found")

        sz_decimals = coin_info.get("szDecimals", 0)
        price_decimal = Decimal(str(price))

        # Rule 1: Max 5 significant figures for non-integers
        if price_decimal != price_decimal.to_integral_value():
            precision = 5 - (price_decimal.adjusted() + 1)
            rounding_exp = Decimal("1e-" + str(precision))
            price_decimal = price_decimal.quantize(rounding_exp, rounding=ROUND_HALF_UP)

        # Rule 2: Max (6 - szDecimals) decimal places
        max_decimal_places = 6 - sz_decimals
        if max_decimal_places >= 0:
            quantize_pattern = Decimal("1e-" + str(max_decimal_places))
            price_decimal = price_decimal.quantize(
                quantize_pattern, rounding=ROUND_HALF_UP
            )

        rounded_price = float(price_decimal)
        logger.debug(f"Rounded price for {coin}: {price} -> {rounded_price}")
        return rounded_price

    def _slippage_price(self, coin: str, is_buy: bool, slippage: float = 0.05) -> float:
        """Calculate price with slippage for market orders."""
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key configuration")
        return self.exchange._slippage_price(coin, is_buy, slippage)

    async def _check_order(self, order_response: Dict[str, Any]) -> bool:
        """Check if order was placed successfully."""
        try:
            if order_response.get("status") != "ok":
                return False

            api_response = (
                order_response.get("response", {}).get("data", {}).get("statuses", [])
            )
            for status in api_response:
                if "error" in status:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking order: {e}")
            return False

    def _extract_order_id(self, order_response: Dict[str, Any]) -> Optional[int]:
        """Extract order ID from order response."""
        try:
            statuses = (
                order_response.get("response", {}).get("data", {}).get("statuses", [])
            )
            for status in statuses:
                if "resting" in status:
                    return status["resting"]["oid"]
                if "filled" in status:
                    return status["filled"]["oid"]
            return None
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Error extracting order ID: {e}")
            return None

    # Order Information Methods (Info API)
    async def get_open_orders(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Get open orders from openOrders endpoint.

        Args:
            user: User address to query (optional)

        Returns:
            Enhanced open orders data
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return {"orders": self.info.frontend_open_orders(user_address)}

    async def get_order_status(
        self, order_id: int, user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the status of a specific order from orderStatus endpoint.

        Args:
            order_id: Order ID to check
            user: User address (optional)

        Returns:
            Enhanced order status information
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return self.info.query_order_by_oid(user_address, order_id)

    async def get_user_fills(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recent user fills/trades from userFills endpoint.

        Args:
            user: User address to query (optional)

        Returns:
            Enhanced user fills data
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return {"fills": self.info.user_fills(user_address)}

    async def get_user_fills_by_time(
        self,
        start_time: int,
        end_time: Optional[int] = None,
        user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get user fills within a specific time range from userFillsByTime endpoint.

        Args:
            start_time: Start time in epoch milliseconds
            end_time: End time in epoch milliseconds (optional)
            user: User address (optional)

        Returns:
            Time-filtered user fills data
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return self.info.user_fills_by_time(user_address, start_time, end_time)

    # Order Trading Methods (Exchange API)
    async def place_order(
        self,
        asset: str,
        is_buy: bool,
        size: float,
        order_type: str = "market",
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place an order using Exchange API.

        Args:
            asset: Asset symbol
            is_buy: True for buy, False for sell
            size: Order size
            order_type: Order type (market, limit, trigger)
            price: Order price (required for limit/trigger)
            time_in_force: Time in force (GTC, IOC, ALO)
            reduce_only: Whether this is a reduce-only order
            take_profit: Take profit price (optional)
            stop_loss: Stop loss price (optional)

        Returns:
            Enhanced order placement result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        response: dict = {
            "main_order": [],
            "stop_loss": [],
            "take_profit": [],
        }

        try:
            # Calculate price for market orders or validate limit price
            if order_type == "market":
                px = self._slippage_price(asset, is_buy, 0.05)
                px = await self.round_to_tick_size(asset, px)
                time_in_force = "IOC"
            elif order_type in ["limit", "trigger"]:
                if price is None:
                    raise ValueError(f"Price is required for {order_type} orders")
                px = await self.round_to_tick_size(asset, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")

            # Validate minimum order value
            estimated_value = size * px
            if estimated_value < 10.0:
                logger.warning(f"Order value ${estimated_value:.2f} below $10 minimum")

            # Convert order type to Hyperliquid format
            tif_map = {"GTC": "Gtc", "IOC": "Ioc", "ALO": "Alo"}
            order_type_map = {
                "limit": {"limit": {"tif": tif_map.get(time_in_force, "Gtc")}},
                "market": {"limit": {"tif": "Ioc"}},
                "trigger": {
                    "trigger": {
                        "triggerPx": px,
                        "tif": tif_map.get(time_in_force, "Gtc"),
                    }
                },
            }

            if order_type not in order_type_map:
                raise ValueError(f"Unsupported order type: {order_type}")

            # Place main order
            logger.info(
                f"Placing {order_type} order: {asset} {'BUY' if is_buy else 'SELL'} {size} @ {px}"
            )
            main_order_result = self.exchange.order(
                asset, is_buy, size, px, order_type_map[order_type], reduce_only, None
            )

            if not await self._check_order(main_order_result):
                raise ValueError(f"Failed to place main order: {main_order_result}")

            main_oid = self._extract_order_id(main_order_result)
            if main_oid:
                response["main_order"] = [main_oid]

            # Place stop loss if specified
            if stop_loss is not None:
                stop_loss_rounded = await self.round_to_tick_size(asset, stop_loss)
                sl_result = self.exchange.order(
                    asset,
                    not is_buy,
                    size,
                    stop_loss_rounded,
                    {
                        "trigger": {
                            "triggerPx": stop_loss_rounded,
                            "isMarket": True,
                            "tpsl": "sl",
                        }
                    },
                    reduce_only=True,
                )

                if await self._check_order(sl_result):
                    sl_oid = self._extract_order_id(sl_result)
                    if sl_oid:
                        response["stop_loss"] = [sl_oid]
                else:
                    logger.warning(f"Failed to place stop loss: {sl_result}")

            # Place take profit if specified
            if take_profit is not None:
                take_profit_rounded = await self.round_to_tick_size(asset, take_profit)
                tp_result = self.exchange.order(
                    asset,
                    not is_buy,
                    size,
                    take_profit_rounded,
                    {
                        "trigger": {
                            "triggerPx": take_profit_rounded,
                            "isMarket": True,
                            "tpsl": "tp",
                        }
                    },
                    reduce_only=True,
                )

                if await self._check_order(tp_result):
                    tp_oid = self._extract_order_id(tp_result)
                    if tp_oid:
                        response["take_profit"] = [tp_oid]
                else:
                    logger.warning(f"Failed to place take profit: {tp_result}")

            # Enhance response
            return {
                "success": True,
                "asset": asset,
                "side": "BUY" if is_buy else "SELL",
                "size": size,
                "price": px,
                "order_type": order_type,
                "time_in_force": time_in_force,
                "reduce_only": reduce_only,
                "estimated_value": estimated_value,
                "order_ids": response,
                "raw_response": main_order_result,
            }

        except Exception as e:
            # Cancel any successfully placed orders if there was an error
            orders_to_cancel = []
            for order_type_key, oids in response.items():
                for oid in oids:
                    if isinstance(oid, int):
                        orders_to_cancel.append({"coin": asset, "oid": oid})

            if orders_to_cancel:
                try:
                    self.exchange.bulk_cancel(orders_to_cancel)
                    logger.info(
                        f"Cancelled {len(orders_to_cancel)} orders due to error"
                    )
                except Exception as cancel_error:
                    logger.error(f"Failed to cancel orders after error: {cancel_error}")

            logger.error(f"Failed to place order: {e}")
            raise

    async def cancel_order(self, asset: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel a specific order using Exchange API.

        Args:
            asset: Asset symbol
            order_id: Order ID to cancel

        Returns:
            Enhanced cancellation result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        result = self.exchange.cancel(asset, order_id)

        return {
            "asset": asset,
            "order_id": order_id,
            "success": result.get("status") == "ok",
            "result": result,
        }

    async def modify_order(
        self,
        asset: str,
        order_id: int,
        new_price: Optional[float] = None,
        new_size: Optional[float] = None,
        new_time_in_force: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Modify an existing order using Exchange API.

        Args:
            asset: Asset symbol
            order_id: Order ID to modify
            new_price: New price (optional)
            new_size: New size (optional)
            new_time_in_force: New time in force (optional)

        Returns:
            Enhanced modification result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        # Get current order info
        user_address = self.user_address or self.wallet_address
        if not user_address:
            raise ValueError("No user address available")

        current_order = self.info.query_order_by_oid(user_address, order_id)
        if current_order.get("status") == "unknownOid":
            raise ValueError(f"Order {order_id} not found")

        # Use current values as defaults
        order_data = current_order.get("order", {}).get("order", {})
        final_is_buy = order_data.get("side") == "B"
        final_size = (
            new_size if new_size is not None else float(order_data.get("origSz", "0"))
        )
        final_price = (
            new_price
            if new_price is not None
            else float(order_data.get("limitPx", "0"))
        )

        # Build order type
        if new_time_in_force:
            tif_map = {"GTC": "Gtc", "IOC": "Ioc", "ALO": "Alo"}
            order_type = {"limit": {"tif": tif_map.get(new_time_in_force, "Gtc")}}
        else:
            order_type = {"limit": {"tif": "Gtc"}}

        result = self.exchange.modify_order(
            oid=order_id,
            name=asset,
            is_buy=final_is_buy,
            sz=final_size,
            limit_px=final_price,
            order_type=order_type,
            reduce_only=False,
        )

        return {
            "asset": asset,
            "order_id": order_id,
            "new_price": new_price,
            "new_size": new_size,
            "new_time_in_force": new_time_in_force,
            "success": result.get("status") == "ok",
            "result": result,
        }

    async def bulk_cancel_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cancel multiple orders at once using Exchange API.

        Args:
            orders: List of orders with 'asset' and 'order_id' fields

        Returns:
            Enhanced bulk cancellation result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        formatted_orders = [
            {"coin": order["asset"], "oid": int(order["order_id"])} for order in orders
        ]

        result = self.exchange.bulk_cancel(formatted_orders)

        return {
            "orders_cancelled": len(formatted_orders),
            "orders": formatted_orders,
            "success": result.get("status") == "ok",
            "result": result,
        }

    async def cancel_all_orders(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel all open orders, optionally filtered by asset using Exchange API.

        Args:
            asset: Asset symbol to filter by (optional)

        Returns:
            Enhanced cancellation result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        user_address = self.user_address or self.wallet_address
        if not user_address:
            raise ValueError("No user address available")

        open_orders = self.info.open_orders(user_address)

        if asset:
            orders_to_cancel = [
                {"coin": order["coin"], "oid": order["oid"]}
                for order in open_orders
                if order.get("coin") == asset
            ]
        else:
            orders_to_cancel = [
                {"coin": order["coin"], "oid": order["oid"]} for order in open_orders
            ]

        if not orders_to_cancel:
            return {
                "orders_cancelled": 0,
                "asset_filter": asset,
                "success": True,
                "message": "No orders to cancel",
            }

        result = self.exchange.bulk_cancel(orders_to_cancel)

        return {
            "orders_cancelled": len(orders_to_cancel),
            "asset_filter": asset,
            "orders": orders_to_cancel,
            "success": result.get("status") == "ok",
            "result": result,
        }
