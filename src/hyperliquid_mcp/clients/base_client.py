"""Base client for Hyperliquid API operations."""

import os
from typing import Optional

from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from hyperliquid_mcp.logging_config import get_logger

logger = get_logger(__name__)


class HyperliquidConnection:
    """Singleton connection manager for Hyperliquid API clients."""

    _instance: Optional["HyperliquidConnection"] = None
    _initialized: bool = False

    def __new__(cls) -> "HyperliquidConnection":
        """Ensure only one connection instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the connection only once."""
        if not HyperliquidConnection._initialized:
            self._info: Optional[Info] = None
            self._exchange: Optional[Exchange] = None
            self._user_address: Optional[str] = None
            self._wallet_address: Optional[str] = None
            self._setup_clients()
            HyperliquidConnection._initialized = True

    def _setup_clients(self) -> None:
        """Setup Hyperliquid API clients."""
        try:
            # Get configuration from environment
            private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
            user_address = os.getenv("HYPERLIQUID_USER_ADDRESS")
            testnet = os.getenv("HYPERLIQUID_TESTNET", "false").lower() == "true"

            # Determine base URL
            base_url = (
                constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
            )

            # Info client (read-only)
            self._info = Info(base_url=base_url, skip_ws=True)

            # Exchange client (requires private key)
            if private_key:
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key

                wallet = Account.from_key(private_key)
                self._exchange = Exchange(wallet=wallet, base_url=base_url)
                self._wallet_address = wallet.address
                logger.info(f"Exchange client initialized with wallet {wallet.address}")
            else:
                logger.warning(
                    "No private key provided - trading operations unavailable"
                )

            # Set user address
            self._user_address = user_address or self._wallet_address

            if self._user_address:
                logger.info(f"Using user address {self._user_address} for queries")

        except Exception as e:
            logger.error(f"Failed to initialize Hyperliquid clients: {e}")
            raise

    @property
    def info(self) -> Info:
        """Get the Info client."""
        if self._info is None:
            raise RuntimeError("Info client not initialized")
        return self._info

    @property
    def exchange(self) -> Exchange:
        """Get the Exchange client."""
        if self._exchange is None:
            raise RuntimeError("Exchange client not initialized - check private key")
        return self._exchange

    @property
    def user_address(self) -> Optional[str]:
        """Get the user address."""
        return self._user_address

    @property
    def wallet_address(self) -> Optional[str]:
        """Get the wallet address."""
        return self._wallet_address

    def is_trading_enabled(self) -> bool:
        """Check if trading operations are available."""
        return self._exchange is not None


class BaseHyperliquidClient:
    """Base client that uses shared connection for Hyperliquid API operations."""

    def __init__(self) -> None:
        """Initialize the base client with shared connection."""
        self._connection = HyperliquidConnection()

    @property
    def info(self) -> Info:
        """Get the Info client from shared connection."""
        return self._connection.info

    @property
    def exchange(self) -> Exchange:
        """Get the Exchange client from shared connection."""
        return self._connection.exchange

    @property
    def user_address(self) -> Optional[str]:
        """Get the user address from shared connection."""
        return self._connection.user_address

    @property
    def wallet_address(self) -> Optional[str]:
        """Get the wallet address from shared connection."""
        return self._connection.wallet_address

    def is_trading_enabled(self) -> bool:
        """Check if trading operations are available."""
        return self._connection.is_trading_enabled()
