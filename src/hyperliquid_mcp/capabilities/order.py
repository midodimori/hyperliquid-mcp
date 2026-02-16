"""Order management tool registrations for Hyperliquid MCP Server."""

from typing import Any, Dict

from fastmcp import FastMCP

from hyperliquid_mcp.clients.order import OrderClient
from hyperliquid_mcp.logging_config import get_logger
from hyperliquid_mcp.models import (
    AssetFilterRequest,
    BulkCancelRequest,
    CancelOrderRequest,
    GetUserFillsRequest,
    ModifyOrderRequest,
    OrderStatusRequest,
    PlaceOrderRequest,
    UserAddressRequest,
)

logger = get_logger(__name__)


def register_order_tools(mcp: FastMCP) -> None:
    """Register order management tools with the MCP server.

    Args:
        mcp: FastMCP server instance.
    """
    order_client = OrderClient()

    @mcp.tool()
    async def place_order(request: PlaceOrderRequest) -> Dict[str, Any]:
        """
        Place an order on Hyperliquid exchange.

        Args:
            request: Order placement request with all order parameters

        Returns:
            Order placement result
        """
        try:
            return await order_client.place_order(
                request.asset,
                request.is_buy,
                request.size,
                request.order_type.value,
                request.price,
                request.time_in_force.value,
                request.reduce_only,
                request.take_profit,
                request.stop_loss,
            )
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_order(request: CancelOrderRequest) -> Dict[str, Any]:
        """
        Cancel an existing order on Hyperliquid exchange.

        Args:
            request: Order cancellation request with asset and order ID

        Returns:
            Cancellation result
        """
        try:
            return await order_client.cancel_order(request.asset, request.order_id)
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_open_orders(request: UserAddressRequest) -> Dict[str, Any]:
        """
        Get open orders from Hyperliquid exchange.

        Args:
            request: User address request with optional user field

        Returns:
            Open orders data
        """
        try:
            return await order_client.get_open_orders(request.user)
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_order_status(request: OrderStatusRequest) -> Dict[str, Any]:
        """
        Get the status of a specific order by order ID.

        Args:
            request: Order status request with order ID and optional user address

        Returns:
            Order status information
        """
        try:
            return await order_client.get_order_status(request.order_id, request.user)
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def modify_order(request: ModifyOrderRequest) -> Dict[str, Any]:
        """
        Modify an existing order on Hyperliquid exchange.

        Args:
            request: Order modification request with asset, order ID, and optional new parameters

        Returns:
            Modification result
        """
        try:
            return await order_client.modify_order(
                request.asset,
                request.order_id,
                request.new_price,
                request.new_size,
                request.new_time_in_force.value if request.new_time_in_force else None,
            )
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def bulk_cancel_orders(request: BulkCancelRequest) -> Dict[str, Any]:
        """
        Cancel multiple orders at once on Hyperliquid exchange.

        Args:
            request: Bulk cancellation request with list of orders to cancel

        Returns:
            Bulk cancellation result
        """
        try:
            return await order_client.bulk_cancel_orders(request.orders)
        except Exception as e:
            logger.error(f"Error bulk canceling orders: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def cancel_all_orders(request: AssetFilterRequest) -> Dict[str, Any]:
        """
        Cancel all open orders, optionally filtered by asset.

        Args:
            request: Asset filter request with optional asset symbol

        Returns:
            Cancellation result
        """
        try:
            return await order_client.cancel_all_orders(request.asset)
        except Exception as e:
            logger.error(f"Error canceling all orders: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_user_fills(request: UserAddressRequest) -> Dict[str, Any]:
        """
        Get recent user fills/trades from Hyperliquid exchange.

        Args:
            request: User address request with optional user field

        Returns:
            User fills data
        """
        try:
            return await order_client.get_user_fills(request.user)
        except Exception as e:
            logger.error(f"Error getting user fills: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_user_fills_by_time(request: GetUserFillsRequest) -> Dict[str, Any]:
        """
        Get user fills/trades within a specific time range from Hyperliquid exchange.

        Args:
            request: User fills request with time range and optional user address

        Returns:
            Time-filtered user fills data
        """
        try:
            return await order_client.get_user_fills_by_time(
                request.start_time, request.end_time, request.user
            )
        except Exception as e:
            logger.error(f"Error getting user fills by time: {e}")
            return {"error": str(e)}
