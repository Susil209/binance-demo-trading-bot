# Binance Futures Testnet Trading Bot

A Python CLI trading bot that places **Market**, **Limit**, and **Stop-Limit** orders on **Binance Futures Testnet (USDT-M)**.

Built with clean architecture, structured logging, and comprehensive error handling.

---

##  Features

- **3 Order Types**: Market, Limit, and Stop-Limit orders
- **Dual CLI Modes**: Command-line flags or interactive menu-driven interface
- **Input Validation**: Comprehensive validation with clear error messages
- **Structured Logging**: Dual logging — colored console + rotating log file
- **Error Handling**: Custom exception hierarchy for API, network, validation, and config errors
- **Dry Run Mode**: Preview orders without placing them
- **Rich UI**: Beautiful terminal output with tables, panels, and color-coded messages

---

## Prerequisites

- Python 3.8+
- Binance Futures Testnet account ([register here](https://testnet.binancefuture.com))
- Testnet API key and secret

---

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd trading_bot
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials

```bash
# Copy the example env file
cp .env.example .env    # Linux/macOS
copy .env.example .env  # Windows
```

Edit `.env` and fill in your Binance Futures Testnet API credentials:

```env
BINANCE_API_KEY=your_actual_api_key
BINANCE_API_SECRET=your_actual_api_secret
```

> **Never commit your `.env` file.** It is already in `.gitignore`.

---

##  Usage

### Command Mode

Place orders directly from the command line:

```bash
# Market buy 0.001 BTC
python -m trading_bot order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit sell 0.001 BTC at $95,000
python -m trading_bot order -s BTCUSDT -S SELL -t LIMIT -q 0.001 -p 95000

# Stop-limit buy (triggers at $95,500, executes at $96,000)
python -m trading_bot order -s BTCUSDT -S BUY -t STOP_LIMIT -q 0.001 -p 96000 --stop-price 95500

# Dry run — preview order without placing
python -m trading_bot order -s BTCUSDT -S BUY -t MARKET -q 0.001 --dry-run
```

### Interactive Mode

Launch the guided menu interface:

```bash
python -m trading_bot interactive
```

You'll be presented with a menu to:
1. Select order type (Market / Limit / Stop-Limit)
2. Enter symbol, side, quantity, and price
3. Review the order summary
4. Confirm or cancel before placing

### CLI Help

```bash
python -m trading_bot --help
python -m trading_bot order --help
```

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package initialization
│   ├── client.py            # Binance API client (HMAC signing, HTTP requests)
│   ├── orders.py            # Order placement logic & response formatting
│   ├── validators.py        # Input validation functions
│   ├── exceptions.py        # Custom exception classes
│   └── logging_config.py    # Dual logging setup (console + file)
├── cli.py                   # CLI entry point (Typer + Rich)
├── config.py                # .env configuration loader
├── __main__.py              # Module entry point
├── logs/                    # Log files (auto-created)
│   └── trading_bot.log
├── .env.example             # API credentials template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Architecture

| Layer         | File(s)                    | Responsibility                       |
| ------------- | -------------------------- | ------------------------------------ |
| **CLI**       | `cli.py`, `__main__.py`    | User interaction, output formatting  |
| **Logic**     | `bot/orders.py`            | Order construction, response parsing |
| **Validation**| `bot/validators.py`        | Input validation with error messages |
| **Client**    | `bot/client.py`            | HTTP requests, HMAC signing, logging |
| **Config**    | `config.py`                | Environment/credential loading       |
| **Errors**    | `bot/exceptions.py`        | Typed exception hierarchy            |
| **Logging**   | `bot/logging_config.py`    | Console + file log configuration     |

---

## Logging

All API requests, responses, and errors are logged to `logs/trading_bot.log`:

- **Console**: INFO level with Rich-formatted colored output
- **File**: DEBUG level with timestamps, module names, and full details
- **Rotation**: Log files rotate at 5 MB (3 backups kept)

Example log entry:
```
[2026-03-28 12:00:00] [INFO    ] [bot.orders.place_market_order] Placing MARKET order: BUY BTCUSDT qty=0.001
[2026-03-28 12:00:01] [INFO    ] [bot.client.place_order] Order placed successfully: orderId=123456 status=FILLED
```

---

## Assumptions

1. **Testnet only**: This bot is configured for Binance Futures Testnet. Do NOT use with real funds without significant additional safeguards.
2. **USDT-M Futures**: Only USDT-margined perpetual futures are supported.
3. **No position management**: The bot places individual orders but does not manage positions, take-profit, or stop-loss strategies.
4. **Time in Force**: Defaults to GTC (Good Till Cancel) for limit orders. Configurable via `--tif` flag.
5. **API rate limits**: No built-in rate limiting. For high-frequency usage, consider adding throttling.

---

## Testing

Run a dry-run to verify everything is configured correctly:

```bash
python -m trading_bot order -s BTCUSDT -S BUY -t MARKET -q 0.001 --dry-run
```

Then place real testnet orders to generate log files:

```bash
# Market order
python -m trading_bot order -s BTCUSDT -S BUY -t MARKET -q 0.001

# Limit order
python -m trading_bot order -s BTCUSDT -S SELL -t LIMIT -q 0.001 -p 95000
```

Check `logs/trading_bot.log` for the full log output.

---

## Dependencies

| Package        | Version  | Purpose                        |
| -------------- | -------- | ------------------------------ |
| `httpx`        | ≥0.27.0  | Modern HTTP client             |
| `typer`        | ≥0.9.0   | CLI framework                  |
| `rich`         | ≥13.0.0  | Beautiful terminal formatting  |
| `python-dotenv`| ≥1.0.0   | .env file loading              |

---

## License

This project is for educational/assessment purposes. Use at your own risk.
