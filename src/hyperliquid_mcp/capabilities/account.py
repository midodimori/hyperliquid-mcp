"""Account tool registrations for Hyperliquid MCP Server."""

from typing import Any, Dict

from fastmcp import FastMCP

from hyperliquid_mcp.clients.account import AccountClient
from hyperliquid_mcp.logging_config import get_logger
from hyperliquid_mcp.models import (
    UpdateLeverageRequest,
    UserAddressRequest,
    WithdrawRequest,
)

logger = get_logger(__name__)


def register_account_tools(mcp: FastMCP) -> None:
    """Register account-related tools with the MCP server.

    Args:
        mcp: FastMCP server instance.
    """
    account_client = AccountClient()

    @mcp.tool()
    async def get_positions(request: UserAddressRequest) -> Dict[str, Any]:
        """
        Get current positions from Hyperliquid exchange.

        Args:
            request: User address request with optional user field

        Returns:
            Current positions and margin information
        """
        try:
            return await account_client.get_positions(request.user)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def update_leverage(request: UpdateLeverageRequest) -> Dict[str, Any]:
        """
        Update leverage for a specific asset on Hyperliquid.

        Args:
            request: Leverage update request with asset, leverage, and margin type

        Returns:
            Leverage update result
        """
        try:
            return await account_client.update_leverage(
                request.asset, request.leverage, request.is_isolated
            )
        except Exception as e:
            logger.error(f"Error updating leverage: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def withdraw(request: WithdrawRequest) -> Dict[str, Any]:
        """
        Withdraw USDC from Hyperliquid to external wallet.

        Args:
            request: Withdrawal request with destination and amount

        Returns:
            Withdrawal result
        """
        try:
            return await account_client.withdraw(request.destination, request.amount)
        except Exception as e:
            logger.error(f"Error withdrawing: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_spot_user_state(request: UserAddressRequest) -> Dict[str, Any]:
        """
        Get spot account state and balances from Hyperliquid.

        Args:
            request: User address request with optional user field

        Returns:
            Spot account state data
        """
        try:
            return await account_client.get_spot_user_state(request.user)
        except Exception as e:
            logger.error(f"Error getting spot user state: {e}")
            return {"error": str(e)}

    @mcp.tool()
    async def get_user_fees(request: UserAddressRequest) -> Dict[str, Any]:
        """
        Get user's fee information from Hyperliquid exchange.

        Args:
            request: User address request with optional user field

        Returns:
            User fee information
        """
        try:
            return await account_client.get_user_fees(request.user)
        except Exception as e:
            logger.error(f"Error getting user fees: {e}")
            return {"error": str(e)}
