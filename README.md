# Hyperliquid MCP Server

A Model Context Protocol (MCP) server that provides comprehensive tools for interacting with the Hyperliquid decentralized exchange. This server enables AI assistants to perform trading operations, manage accounts, and retrieve market data through a standardized interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.10.6+-green.svg)](https://github.com/jlowin/fastmcp)

## 🚀 Features

- **Account Management** - Positions, balances, transfers, and leverage control
- **Order Management** - Place, cancel, modify orders with advanced features
- **Market Data** - Real-time prices, orderbooks, candles, and funding rates
- **Multiple Transports** - stdio, HTTP (Streamable HTTP), and SSE support
- **Risk Management** - Comprehensive validation and error handling
- **Type Safety** - Full Pydantic validation for all inputs
- **Error Handling** - Comprehensive error reporting and logging

## 📦 Installation

### Using uvx (Recommended)

```bash
# Run with stdio (default)
uvx hyperliquid-mcp

# Run with HTTP transport
uvx hyperliquid-mcp --transport http --port 3000

# Run with SSE transport
uvx hyperliquid-mcp --transport sse --port 3000
```

### Using uv

```bash
uv add hyperliquid-mcp
uv run hyperliquid-mcp
```

### Using pip

```bash
pip install hyperliquid-mcp
hyperliquid-mcp
```

### CLI Options

```
hyperliquid-mcp [OPTIONS]

Options:
  --transport, -t {stdio,http,sse}  Transport type (default: stdio)
  --host HOST                       Host to bind to (default: localhost)
  --port, -p PORT                   Port to listen on (default: 3000)
  --log-level, -l {debug,info,warn,error}  Log level (default: info)
  --version, -v                     Show version and exit
```

## ⚙️ Configuration

### Environment Variables

Configure the following environment variables:

```bash
# Required for trading operations
export HYPERLIQUID_PRIVATE_KEY="your_private_key_here"

# Optional: Specify a different user address for queries (defaults to wallet address)
export HYPERLIQUID_USER_ADDRESS="0x1234567890123456789012345678901234567890"

# Optional: Use testnet instead of mainnet (default: false)
export HYPERLIQUID_TESTNET="true"

# Optional: Show detailed logs for debugging (default: false)
export HYPERLIQUID_MCP_SHOW_LOGS="false"
```

> ⚠️ **Security Warning**: Never share your private key. The server will warn if the key is missing but will still start in read-only mode for market data.

#### Environment Variable Details

- **`HYPERLIQUID_PRIVATE_KEY`** (Required for trading): Your wallet's private key for signing transactions
- **`HYPERLIQUID_USER_ADDRESS`** (Optional): Ethereum address to query data for. If not set, uses the address derived from your private key
- **`HYPERLIQUID_TESTNET`** (Optional): Set to `"true"` to use Hyperliquid's testnet for development and testing
- **`HYPERLIQUID_MCP_SHOW_LOGS`** (Optional): Set to `"true"` to enable detailed logging for debugging and development

### 👤 User Address Configuration

The server supports querying data for different users:

- **Default behavior**: Uses the address derived from your `HYPERLIQUID_PRIVATE_KEY`
- **Custom user**: Set `HYPERLIQUID_USER_ADDRESS` to query a different address
- **Tool-level override**: Many tools accept a `user` parameter to query specific addresses

**Use cases:**
- Monitor multiple accounts from one server instance
- Query public data for other traders (positions, fills, etc.)
- Portfolio management for multiple wallets
- Analytics and research on other users' trading activity

### 🧪 Testnet Configuration

For development and testing, you can use Hyperliquid's testnet:

1. **Enable testnet mode** by setting `HYPERLIQUID_TESTNET=true`
2. **Get testnet tokens** from the [Hyperliquid testnet faucet](https://app.hyperliquid-testnet.xyz/faucet)
3. **Use testnet-specific addresses** - testnet has separate contracts and addresses
4. **Test safely** - All trades execute on testnet without real financial risk

> 💡 **Tip**: Always test your trading strategies on testnet before using real funds on mainnet.

### Claude Desktop Configuration

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hyperliquid": {
      "command": "uvx",
      "args": ["--no-progress","hyperliquid-mcp"],
      "env": {
        "HYPERLIQUID_PRIVATE_KEY": "your_private_key_here",
        "HYPERLIQUID_USER_ADDRESS": "0x1234567890123456789012345678901234567890",
        "HYPERLIQUID_TESTNET": "false",
        "HYPERLIQUID_MCP_SHOW_LOGS": "false"
      },
      "transport": "stdio"
    }
  }
}
```

### Alternative Configurations

#### Using uv directly:
```json
{
  "mcpServers": {
    "hyperliquid": {
      "command": "uv",
      "args": ["run", "--with", "hyperliquid-mcp", "hyperliquid-mcp"],
      "env": {
        "HYPERLIQUID_PRIVATE_KEY": "your_private_key_here",
        "HYPERLIQUID_USER_ADDRESS": "0x1234567890123456789012345678901234567890",
        "HYPERLIQUID_TESTNET": "false",
        "HYPERLIQUID_MCP_SHOW_LOGS": "false"
      },
      "transport": "stdio"
    }
  }
}
```

#### HTTP transport (for remote/multi-client setups):

> ⚠️ **Note**: Environment variables (`HYPERLIQUID_PRIVATE_KEY`, etc.) must be exported in the shell where the server is started — they are **not** passed via the client config like with stdio.

```bash
# 1. Export env vars in your terminal
export HYPERLIQUID_PRIVATE_KEY="your_private_key_here"
export HYPERLIQUID_TESTNET="false"

# 2. Start the server
hyperliquid-mcp --transport http --port 3000
```

Then configure your MCP client to connect:
```json
{
  "mcpServers": {
    "hyperliquid": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

#### Local development:
```json
{
  "mcpServers": {
    "hyperliquid": {
      "command": "uv",
      "args": ["run", "hyperliquid-mcp"],
      "cwd": "/path/to/hyperliquid-mcp",
      "env": {
        "HYPERLIQUID_PRIVATE_KEY": "your_private_key_here",
        "HYPERLIQUID_USER_ADDRESS": "0x1234567890123456789012345678901234567890",
        "HYPERLIQUID_TESTNET": "true",
        "HYPERLIQUID_MCP_SHOW_LOGS": "true"
      },
      "transport": "stdio"
    }
  }
}
```

## 🛠️ Available Tools

### 👤 Account Management (5 tools)

#### `get_positions`
Get current trading positions and margin information.
- **Input**: `user` (optional) - Ethereum address to query (defaults to `HYPERLIQUID_USER_ADDRESS` or wallet address)
- **Output**: Positions and margin summary data

#### `update_leverage`
Modify leverage settings for a specific asset.
- **Input**: `asset`, `leverage` (1-100), `is_isolated` (boolean)
- **Output**: Leverage update confirmation

#### `withdraw`
Withdraw USDC to an external wallet.
- **Input**: `destination` (Ethereum address), `amount` (minimum $1.01)
- **Output**: Withdrawal confirmation

#### `get_spot_user_state`
Get spot trading account balances and state.
- **Input**: `user` (optional) - Ethereum address to query
- **Output**: Spot account balances and state

#### `get_user_fees`
Get user's current fee structure and rates.
- **Input**: `user` (optional) - Ethereum address to query
- **Output**: Fee information and tier details

### 📊 Market Data (5 tools)

#### `get_market_data`
Get current market data for a specific asset.
- **Input**: `asset` - Asset symbol (e.g., "BTC", "ETH")
- **Output**: Current price, volume, and market statistics

#### `get_candle_data`
Get historical OHLCV candlestick data.
- **Input**: `asset`, `interval` (1m, 5m, 1h, 1d, etc.), `start_time`, `end_time`
- **Output**: Historical price candles

#### `get_l2_orderbook`
Get Level 2 order book depth data.
- **Input**: `asset`, `significant_figures` (optional, 1-10)
- **Output**: Bid/ask levels with quantities

#### `get_funding_rates`
Retrieve current and historical funding rates for perpetual contracts.
- **Input**: `asset` (optional), `include_history` (boolean), `start_time` (optional)
- **Output**: Funding rate data

#### `calculate_min_order_size`
Calculate minimum order size for an asset to meet value requirements.
- **Input**: `asset`, `min_value_usd` (default: $10)
- **Output**: Minimum order size calculation

### 📈 Order Management (9 tools)

#### `place_order`
Place a new trading order on the exchange.
- **Input**: Order details including:
  - `asset` - Asset symbol
  - `is_buy` - Order direction (boolean)
  - `size` - Order quantity
  - `order_type` - "market", "limit", or "trigger"
  - `price` - Order price (required for limit/trigger)
  - `time_in_force` - "GTC", "IOC", or "ALO"
  - `reduce_only` - Reduce-only flag (boolean)
  - `take_profit` - Take profit price (optional)
  - `stop_loss` - Stop loss price (optional)
- **Output**: Order placement confirmation with order ID

#### `cancel_order`
Cancel an existing order.
- **Input**: `asset`, `order_id`
- **Output**: Cancellation confirmation

#### `modify_order`
Modify price, size, or time-in-force of an existing order.
- **Input**: `asset`, `order_id`, `new_price` (optional), `new_size` (optional), `new_time_in_force` (optional)
- **Output**: Modification confirmation

#### `get_open_orders`
Retrieve all currently open orders.
- **Input**: `user` (optional) - Ethereum address to query
- **Output**: List of open orders with details

#### `get_order_status`
Check the status of a specific order.
- **Input**: `order_id`, `user` (optional)
- **Output**: Order status and execution details

#### `bulk_cancel_orders`
Cancel multiple orders in a single request.
- **Input**: `orders` - List of orders with asset and order_id
- **Output**: Bulk cancellation results

#### `cancel_all_orders`
Cancel all open orders, optionally filtered by asset.
- **Input**: `asset` (optional) - Filter by specific asset
- **Output**: Mass cancellation confirmation

#### `get_user_fills`
Get recent trade executions (fills).
- **Input**: `user` (optional) - Ethereum address to query
- **Output**: Recent trade execution data

#### `get_user_fills_by_time`
Get user's trade fills within a specific time range.
- **Input**: `start_time`, `end_time` (optional), `user` (optional)
- **Output**: Trade execution history

## 🧪 Testing

The project includes comprehensive tests covering all tools:

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test categories (use direct command for specific targets)
uv run pytest tests/test_server.py::TestAccountTools -v
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/midodimori/hyperliquid-mcp.git
cd hyperliquid-mcp

# Install with development dependencies
make install-dev

# Run tests
make test

# Format and lint code
make format

# Check code style and types
make lint

# Run the server locally
make run

# See all available commands
make help
```

### Project Structure

```
hyperliquid-mcp/
├── src/hyperliquid_mcp/
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point (argparse)
│   ├── server.py          # Server factory (create_server)
│   ├── config.py          # Pydantic configuration models
│   ├── models.py          # Request/response models
│   ├── logging_config.py  # Logging configuration
│   ├── capabilities/      # MCP tool registrations
│   │   ├── account.py     # Account tools (5)
│   │   ├── market.py      # Market data tools (5)
│   │   └── order.py       # Order management tools (9)
│   ├── clients/           # Hyperliquid API clients
│   │   ├── base_client.py # Base client & connection
│   │   ├── account.py     # Account operations
│   │   ├── market.py      # Market data operations
│   │   └── order.py       # Order operations
│   └── transports/        # Transport runners
│       ├── stdio.py       # stdio transport (default)
│       ├── http.py        # Streamable HTTP transport
│       └── sse.py         # SSE transport
├── tests/
│   ├── test_server.py     # Tool function tests
│   └── test_mcp_integration.py  # MCP integration tests
├── pyproject.toml         # Project configuration
└── README.md
```

## 📚 API Reference

### Order Types
- **market**: Execute immediately at current market price
- **limit**: Execute only at specified price or better
- **trigger**: Stop/trigger order that becomes market order when triggered

### Time in Force
- **GTC** (Good Till Cancelled): Order remains active until filled or cancelled
- **IOC** (Immediate or Cancel): Fill immediately or cancel unfilled portion
- **ALO** (Add Liquidity Only): Only add liquidity, don't take from order book

### Candle Intervals
Supported intervals: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided for educational and informational purposes only. Trading cryptocurrencies involves substantial risk and may result in significant financial losses. The authors are not responsible for any trading losses incurred through the use of this software. Always conduct your own research and consider consulting with a qualified financial advisor before making trading decisions.

## 🔗 Links

- [Hyperliquid Exchange](https://hyperliquid.xyz/)
- [Hyperliquid Documentation](https://hyperliquid.gitbook.io/hyperliquid-docs)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Claude Desktop](https://claude.ai/desktop)

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the [Hyperliquid Discord](https://discord.gg/hyperliquid) for community support
- Review the comprehensive test suite for usage examples