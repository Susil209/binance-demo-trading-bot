"""Binance Futures Testnet API client.

Handles HMAC-SHA256 signing, HTTP requests, and response parsing.
All requests and responses are logged for debugging.
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx

from bot.exceptions import BinanceAPIError, NetworkError

logger = logging.getLogger("bot.client")


class BinanceClient:
    """Low-level client for Binance Futures Testnet REST API.

    Handles authentication (HMAC-SHA256 signatures), request construction,
    and response parsing. All API interactions are logged.

    Args:
        api_key: Binance API key.
        api_secret: Binance API secret.
        base_url: Testnet base URL.
        timeout: Request timeout in seconds.
    """

    # API endpoints
    ORDER_ENDPOINT = "/fapi/v1/order"
    EXCHANGE_INFO_ENDPOINT = "/fapi/v1/exchangeInfo"
    SERVER_TIME_ENDPOINT = "/fapi/v1/time"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://testnet.binancefuture.com",
        timeout: float = 30.0,
    ):
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._time_offset: int = 0  # ms offset between local and server time
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        # Sync local clock with Binance server time
        self._sync_time()
        logger.info("Binance client initialized (base_url=%s, time_offset=%dms)", self._base_url, self._time_offset)

    def _generate_signature(self, query_string: str) -> str:
        """Create HMAC-SHA256 signature for the query string.

        Args:
            query_string: URL-encoded parameter string.

        Returns:
            Hex-encoded HMAC-SHA256 signature.
        """
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _sync_time(self) -> None:
        """Synchronize local clock with Binance server time.

        Calculates the offset between the local system clock and
        Binance's server clock. This offset is applied to all
        subsequent signed requests to avoid -1021 timestamp errors.
        """
        try:
            local_time = int(time.time() * 1000)
            response = self._client.request("GET", self.SERVER_TIME_ENDPOINT)
            server_time = response.json().get("serverTime", local_time)
            self._time_offset = server_time - local_time
            logger.debug(
                "Time synced: server=%d local=%d offset=%dms",
                server_time, local_time, self._time_offset,
            )
        except Exception as e:
            logger.warning("Failed to sync server time, using local clock: %s", e)
            self._time_offset = 0

    def _get_timestamp(self) -> int:
        """Get adjusted timestamp in milliseconds using server time offset."""
        return int(time.time() * 1000) + self._time_offset

    def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a signed API request.

        Adds timestamp and HMAC signature to the request parameters.

        Args:
            method: HTTP method ('GET', 'POST', 'DELETE').
            endpoint: API endpoint path.
            params: Request parameters (will be signed).

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            BinanceAPIError: On API error response.
            NetworkError: On connection/timeout failure.
        """
        if params is None:
            params = {}

        # Add timestamp for signature
        params["timestamp"] = self._get_timestamp()

        # Build query string and sign it
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        query_string += f"&signature={signature}"

        url = f"{endpoint}?{query_string}"

        logger.debug(
            "API Request: %s %s | params=%s",
            method,
            endpoint,
            {k: v for k, v in params.items() if k != "timestamp"},
        )

        try:
            response = self._client.request(method, url)
        except httpx.ConnectError as e:
            logger.error("Connection failed: %s", e)
            raise NetworkError(f"Failed to connect to {self._base_url}: {e}") from e
        except httpx.TimeoutException as e:
            logger.error("Request timed out: %s", e)
            raise NetworkError(f"Request timed out: {e}") from e
        except httpx.HTTPError as e:
            logger.error("HTTP error: %s", e)
            raise NetworkError(f"HTTP error: {e}") from e

        # Parse response
        try:
            data = response.json()
        except Exception:
            logger.error(
                "Failed to parse response (status=%d): %s",
                response.status_code,
                response.text[:500],
            )
            raise BinanceAPIError(
                status_code=response.status_code,
                error_code=-1,
                error_message=f"Invalid JSON response: {response.text[:200]}",
            )

        # Check for API errors
        if response.status_code >= 400:
            error_code = data.get("code", -1)
            error_msg = data.get("msg", "Unknown error")
            logger.error(
                "API Error [%d] (code %d): %s",
                response.status_code,
                error_code,
                error_msg,
            )
            raise BinanceAPIError(
                status_code=response.status_code,
                error_code=error_code,
                error_message=error_msg,
            )

        logger.debug("API Response [%d]: %s", response.status_code, data)
        return data

    def _public_request(
        self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an unsigned (public) API request.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            BinanceAPIError: On API error response.
            NetworkError: On connection/timeout failure.
        """
        logger.debug("Public API Request: %s %s", method, endpoint)

        try:
            response = self._client.request(method, endpoint, params=params)
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self._base_url}: {e}") from e
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise NetworkError(f"HTTP error: {e}") from e

        data = response.json()

        if response.status_code >= 400:
            raise BinanceAPIError(
                status_code=response.status_code,
                error_code=data.get("code", -1),
                error_message=data.get("msg", "Unknown error"),
            )

        return data

    # ── Public API Methods ──────────────────────────────────────────────

    def place_order(self, **params) -> Dict[str, Any]:
        """Place an order on Binance Futures.

        Args:
            **params: Order parameters (symbol, side, type, quantity, etc.).

        Returns:
            Order response from Binance API.
        """
        logger.info(
            "Placing order: %s %s %s qty=%s",
            params.get("type", "?"),
            params.get("side", "?"),
            params.get("symbol", "?"),
            params.get("quantity", "?"),
        )
        result = self._signed_request("POST", self.ORDER_ENDPOINT, params)
        logger.info(
            "Order placed successfully: orderId=%s status=%s",
            result.get("orderId"),
            result.get("status"),
        )
        return result

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange information (available symbols, rules, etc.)."""
        return self._public_request("GET", self.EXCHANGE_INFO_ENDPOINT)

    def close(self) -> None:
        """Close the HTTP client connection."""
        self._client.close()
        logger.debug("Binance client connection closed.")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
