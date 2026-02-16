"""Account-related operations for Hyperliquid API."""

from typing import Any, Dict, Optional

from hyperliquid_mcp.clients.base_client import BaseHyperliquidClient
from hyperliquid_mcp.logging_config import get_logger

logger = get_logger(__name__)


class AccountClient(BaseHyperliquidClient):
    """Client for account-related operations using Hyperliquid Info and Exchange APIs."""

    # Account Information Methods
    async def get_positions(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current positions from clearinghouseState.

        Args:
            user: User address to query (optional)

        Returns:
            Enhanced positions data with margin summary
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return self.info.user_state(user_address)

    async def get_user_fees(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user's fee information from userFees endpoint.

        Args:
            user: User address to query (optional)

        Returns:
            Raw user fee information including fee schedule, discounts, and daily volume
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return self.info.user_fees(user_address)

    async def get_spot_user_state(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Get spot account state from spotClearinghouseState.

        Args:
            user: User address to query (optional)

        Returns:
            Spot account state with token balances
        """
        user_address = user or self.user_address
        if not user_address:
            raise ValueError("No user address available")

        return self.info.spot_user_state(user_address)

    # Leverage and Account Management
    async def update_leverage(
        self, asset: str, leverage: float, is_isolated: bool = True
    ) -> Dict[str, Any]:
        """
        Update leverage for an asset using Exchange API.

        Args:
            asset: Asset symbol
            leverage: New leverage value
            is_isolated: Whether to use isolated margin

        Returns:
            Leverage update result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        leverage_int = int(leverage)
        is_cross = not is_isolated

        return self.exchange.update_leverage(leverage_int, asset, is_cross)

    async def withdraw(self, destination: str, amount: float) -> Dict[str, Any]:
        """
        Initiate withdrawal to external wallet using Exchange API.

        Args:
            destination: Destination wallet address
            amount: Amount to withdraw

        Returns:
            Withdrawal result
        """
        if not self.is_trading_enabled():
            raise RuntimeError("Trading not enabled - check private key")

        if amount <= 1.0:
            raise ValueError(
                "Withdrawal amount must be greater than $1.00 (withdrawal fee)"
            )

        return self.exchange.withdraw_from_bridge(
            amount=amount,
            destination=destination,
        )
