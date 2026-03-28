"""Order placement logic for Binance Futures.

Provides high-level functions for placing Market, Limit, and Stop-Limit orders.
Handles parameter construction and response formatting.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from bot.client import BinanceClient
from bot.validators import validate_all

logger = logging.getLogger("bot.orders")


@dataclass
class OrderResult:
    """Structured representation of an order response.

    Attributes:
        order_id: Binance order ID.
        symbol: Trading pair symbol.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_LIMIT.
        status: Order status (e.g., NEW, FILLED).
        quantity: Ordered quantity.
        executed_qty: Quantity filled so far.
        price: Limit price (if applicable).
        avg_price: Average fill price.
        time_in_force: Time in force (GTC, IOC, FOK).
        raw_response: Full API response dictionary.
    """

    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: str
    executed_qty: str
    price: str
    avg_price: str
    time_in_force: str
    raw_response: Dict[str, Any]

    @classmethod
    def from_api_response(cls, response: Dict[str, Any]) -> "OrderResult":
        """Create an OrderResult from a raw Binance API response.

        Args:
            response: Raw JSON response from the Binance API.

        Returns:
            Parsed OrderResult instance.
        """
        return cls(
            order_id=response.get("orderId", 0),
            symbol=response.get("symbol", ""),
            side=response.get("side", ""),
            order_type=response.get("type", ""),
            status=response.get("status", ""),
            quantity=response.get("origQty", "0"),
            executed_qty=response.get("executedQty", "0"),
            price=response.get("price", "0"),
            avg_price=response.get("avgPrice", "0"),
            time_in_force=response.get("timeInForce", ""),
            raw_response=response,
        )


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
) -> OrderResult:
    """Place a market order.

    Args:
        client: Initialized BinanceClient.
        symbol: Trading pair (e.g., BTCUSDT).
        side: BUY or SELL.
        quantity: Amount to trade.

    Returns:
        OrderResult with order details.
    """
    params = validate_all(
        symbol=symbol, side=side, order_type="MARKET", quantity=quantity
    )

    logger.info(
        "Placing MARKET order: %s %s qty=%s",
        params["side"],
        params["symbol"],
        params["quantity"],
    )

    response = client.place_order(
        symbol=params["symbol"],
        side=params["side"],
        type="MARKET",
        quantity=params["quantity"],
    )

    result = OrderResult.from_api_response(response)
    logger.info(
        "MARKET order result: orderId=%s status=%s executedQty=%s avgPrice=%s",
        result.order_id,
        result.status,
        result.executed_qty,
        result.avg_price,
    )
    return result


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> OrderResult:
    """Place a limit order.

    Args:
        client: Initialized BinanceClient.
        symbol: Trading pair (e.g., BTCUSDT).
        side: BUY or SELL.
        quantity: Amount to trade.
        price: Limit price.
        time_in_force: Time in force (default: GTC — Good Till Cancel).

    Returns:
        OrderResult with order details.
    """
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type="LIMIT",
        quantity=quantity,
        price=price,
    )

    logger.info(
        "Placing LIMIT order: %s %s qty=%s price=%s tif=%s",
        params["side"],
        params["symbol"],
        params["quantity"],
        params["price"],
        time_in_force,
    )

    response = client.place_order(
        symbol=params["symbol"],
        side=params["side"],
        type="LIMIT",
        quantity=params["quantity"],
        price=params["price"],
        timeInForce=time_in_force,
    )

    result = OrderResult.from_api_response(response)
    logger.info(
        "LIMIT order result: orderId=%s status=%s price=%s",
        result.order_id,
        result.status,
        result.price,
    )
    return result


def place_stop_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
    time_in_force: str = "GTC",
) -> OrderResult:
    """Place a stop-limit order (bonus feature).

    The order becomes a limit order once the stop_price is reached.

    Args:
        client: Initialized BinanceClient.
        symbol: Trading pair (e.g., BTCUSDT).
        side: BUY or SELL.
        quantity: Amount to trade.
        price: Limit price (the price the order will execute at).
        stop_price: Trigger price (when market reaches this, the limit order activates).
        time_in_force: Time in force (default: GTC).

    Returns:
        OrderResult with order details.
    """
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type="STOP_LIMIT",
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    logger.info(
        "Placing STOP_LIMIT order: %s %s qty=%s price=%s stopPrice=%s tif=%s",
        params["side"],
        params["symbol"],
        params["quantity"],
        params["price"],
        params["stop_price"],
        time_in_force,
    )

    # Binance API uses "STOP" type with a stopPrice param for stop-limit orders
    response = client.place_order(
        symbol=params["symbol"],
        side=params["side"],
        type="STOP",
        quantity=params["quantity"],
        price=params["price"],
        stopPrice=params["stop_price"],
        timeInForce=time_in_force,
    )

    result = OrderResult.from_api_response(response)
    logger.info(
        "STOP_LIMIT order result: orderId=%s status=%s price=%s",
        result.order_id,
        result.status,
        result.price,
    )
    return result


# Dispatcher for CLI convenience
ORDER_HANDLERS = {
    "MARKET": place_market_order,
    "LIMIT": place_limit_order,
    "STOP_LIMIT": place_stop_limit_order,
}


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
    time_in_force: str = "GTC",
) -> OrderResult:
    """Unified order placement — dispatches to the appropriate handler.

    Args:
        client: Initialized BinanceClient.
        symbol: Trading pair.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_LIMIT.
        quantity: Amount to trade.
        price: Limit price (for LIMIT/STOP_LIMIT).
        stop_price: Stop trigger price (for STOP_LIMIT).
        time_in_force: Time in force (default: GTC).

    Returns:
        OrderResult with order details.
    """
    normalized_type = order_type.strip().upper().replace("-", "_")

    if normalized_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)
    elif normalized_type == "LIMIT":
        return place_limit_order(client, symbol, side, quantity, price, time_in_force)
    elif normalized_type == "STOP_LIMIT":
        return place_stop_limit_order(
            client, symbol, side, quantity, price, stop_price, time_in_force
        )
    else:
        from bot.exceptions import ValidationError

        raise ValidationError(f"Unknown order type: {order_type}")
