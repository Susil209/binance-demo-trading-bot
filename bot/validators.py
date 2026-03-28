"""Input validation for trading bot parameters.

All validators raise ValidationError with descriptive messages on failure.
"""

import re
from typing import Optional

from bot.exceptions import ValidationError


# Binance symbol pattern: uppercase letters only, typically 6-12 chars (e.g., BTCUSDT)
_SYMBOL_PATTERN = re.compile(r"^[A-Z]{2,20}$")

VALID_SIDES = ("BUY", "SELL")
VALID_ORDER_TYPES = ("MARKET", "LIMIT", "STOP_LIMIT")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a trading symbol.

    Args:
        symbol: Trading pair symbol (e.g., 'btcusdt' or 'BTCUSDT').

    Returns:
        Uppercased symbol string.

    Raises:
        ValidationError: If symbol is empty or has invalid format.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty.")

    normalized = symbol.strip().upper()

    if not _SYMBOL_PATTERN.match(normalized):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. "
            "Symbol must contain only letters (e.g., BTCUSDT, ETHUSDT)."
        )

    return normalized


def validate_side(side: str) -> str:
    """Validate order side.

    Args:
        side: Order side ('BUY' or 'SELL').

    Returns:
        Uppercased side string.

    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    if not side or not side.strip():
        raise ValidationError("Side cannot be empty.")

    normalized = side.strip().upper()

    if normalized not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )

    return normalized


def validate_order_type(order_type: str) -> str:
    """Validate order type.

    Args:
        order_type: Type of order ('MARKET', 'LIMIT', or 'STOP_LIMIT').

    Returns:
        Uppercased order type string.

    Raises:
        ValidationError: If order type is not recognized.
    """
    if not order_type or not order_type.strip():
        raise ValidationError("Order type cannot be empty.")

    normalized = order_type.strip().upper().replace("-", "_")

    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )

    return normalized


def validate_quantity(quantity: float) -> float:
    """Validate order quantity.

    Args:
        quantity: Amount to trade. Must be a positive number.

    Returns:
        The validated quantity as a float.

    Raises:
        ValidationError: If quantity is not positive.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Invalid quantity '{quantity}'. Must be a positive number."
        )

    if qty <= 0:
        raise ValidationError(
            f"Quantity must be greater than 0, got {qty}."
        )

    return qty


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """Validate price based on order type.

    Price is required for LIMIT and STOP_LIMIT orders, ignored for MARKET.

    Args:
        price: Order price. Required for LIMIT/STOP_LIMIT.
        order_type: Already-validated order type string.

    Returns:
        Validated price as float, or None for MARKET orders.

    Raises:
        ValidationError: If price is missing/invalid for LIMIT/STOP_LIMIT orders.
    """
    needs_price = order_type in ("LIMIT", "STOP_LIMIT")

    if not needs_price:
        return None

    if price is None:
        raise ValidationError(
            f"Price is required for {order_type} orders."
        )

    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Invalid price '{price}'. Must be a positive number."
        )

    if p <= 0:
        raise ValidationError(
            f"Price must be greater than 0, got {p}."
        )

    return p


def validate_stop_price(
    stop_price: Optional[float], order_type: str
) -> Optional[float]:
    """Validate stop price for STOP_LIMIT orders.

    Args:
        stop_price: Trigger price for stop-limit orders.
        order_type: Already-validated order type string.

    Returns:
        Validated stop price as float, or None for non-stop orders.

    Raises:
        ValidationError: If stop price is missing/invalid for STOP_LIMIT orders.
    """
    if order_type != "STOP_LIMIT":
        return None

    if stop_price is None:
        raise ValidationError("Stop price is required for STOP_LIMIT orders.")

    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Invalid stop price '{stop_price}'. Must be a positive number."
        )

    if sp <= 0:
        raise ValidationError(
            f"Stop price must be greater than 0, got {sp}."
        )

    return sp


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """Run all validations and return a dict of cleaned parameters.

    Args:
        symbol: Trading pair symbol.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP_LIMIT.
        quantity: Amount to trade.
        price: Limit price (required for LIMIT/STOP_LIMIT).
        stop_price: Stop trigger price (required for STOP_LIMIT).

    Returns:
        Dictionary with validated and normalized parameters.

    Raises:
        ValidationError: On any validation failure.
    """
    validated_type = validate_order_type(order_type)

    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validated_type,
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, validated_type),
        "stop_price": validate_stop_price(stop_price, validated_type),
    }
