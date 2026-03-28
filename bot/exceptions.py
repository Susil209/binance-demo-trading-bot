"""Custom exception classes for the trading bot."""


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""

    pass


class ConfigError(TradingBotError):
    """Raised when configuration is missing or invalid.

    Examples: missing API key/secret, invalid .env file.
    """

    pass


class ValidationError(TradingBotError):
    """Raised when user input fails validation.

    Examples: invalid symbol format, negative quantity, missing price for LIMIT order.
    """

    pass


class BinanceAPIError(TradingBotError):
    """Raised when Binance API returns an error response.

    Attributes:
        status_code: HTTP status code from the API.
        error_code: Binance-specific error code (e.g., -1121).
        error_message: Human-readable error message from Binance.
    """

    def __init__(self, status_code: int, error_code: int, error_message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(
            f"Binance API Error [{status_code}] (code {error_code}): {error_message}"
        )


class NetworkError(TradingBotError):
    """Raised when a network-level failure occurs.

    Examples: connection timeout, DNS resolution failure, connection refused.
    """

    pass
