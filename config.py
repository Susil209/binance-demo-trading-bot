"""Configuration loader for the trading bot.

Loads API credentials from .env file or environment variables.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from bot.exceptions import ConfigError


@dataclass(frozen=True)
class BotConfig:
    """Immutable configuration for the trading bot."""

    api_key: str
    api_secret: str
    base_url: str = "https://testnet.binancefuture.com"


def load_config() -> BotConfig:
    """Load configuration from .env file and environment variables.

    Searches for .env in the current directory and parent directories.

    Returns:
        BotConfig with validated credentials.

    Raises:
        ConfigError: If API key or secret is missing.
    """
    # Load .env file (does not override existing env vars)
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or api_key == "your_api_key_here":
        raise ConfigError(
            "BINANCE_API_KEY is not set. "
            "Please copy .env.example to .env and fill in your testnet API key."
        )

    if not api_secret or api_secret == "your_api_secret_here":
        raise ConfigError(
            "BINANCE_API_SECRET is not set. "
            "Please copy .env.example to .env and fill in your testnet API secret."
        )

    return BotConfig(api_key=api_key, api_secret=api_secret)
