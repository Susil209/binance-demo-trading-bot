"""CLI entry point for the Binance Futures Trading Bot.

Provides two modes:
  - Command mode:  python -m trading_bot order --symbol BTCUSDT --side BUY ...
  - Interactive mode: python -m trading_bot interactive
"""

import sys
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, FloatPrompt
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClient
from bot.exceptions import (
    BinanceAPIError,
    ConfigError,
    NetworkError,
    TradingBotError,
    ValidationError,
)
from bot.logging_config import setup_logging
from bot.orders import OrderResult, place_order
from config import load_config

# ── App Setup ───────────────────────────────────────────────────────────

# Fix Windows console Unicode encoding (enables emoji/special chars)
import sys
if sys.platform == "win32":
    import os
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # Fallback: some environments don't support reconfigure

app = typer.Typer(
    name="trading-bot",
    help="Binance Futures Testnet Trading Bot -- Place MARKET, LIMIT, and STOP_LIMIT orders.",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()
logger = logging.getLogger("bot.cli")


# ── Helper Functions ────────────────────────────────────────────────────


def _print_banner() -> None:
    """Display the application banner."""
    banner = Text()
    banner.append("╔══════════════════════════════════════════════╗\n", style="cyan")
    banner.append("║   ", style="cyan")
    banner.append("║ Binance Futures Testnet Trading Bot", style="bold white")
    banner.append("║\n", style="cyan")
    banner.append("║   ", style="cyan")
    banner.append("║     USDT-M Perpetual Futures", style="dim white")
    banner.append("║\n", style="cyan")
    banner.append("╚══════════════════════════════════════════════╝", style="cyan")
    console.print(banner)
    console.print()


def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    stop_price: Optional[float],
) -> None:
    """Print the order request summary as a Rich table."""
    table = Table(
        title="Order Request Summary",
        title_style="bold yellow",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("Parameter", style="white", min_width=14)
    table.add_column("Value", style="bold green", min_width=20)

    table.add_row("Symbol", symbol)
    side_color = "green" if side == "BUY" else "red"
    table.add_row("Side", f"[bold {side_color}]{side}[/bold {side_color}]")
    table.add_row("Order Type", order_type)
    table.add_row("Quantity", str(quantity))

    if price is not None:
        table.add_row("Price", str(price))
    if stop_price is not None:
        table.add_row("Stop Price", str(stop_price))

    console.print(table)
    console.print()


def _print_order_result(result: OrderResult) -> None:
    """Print order response details as a Rich table."""
    table = Table(
        title="✅ Order Response",
        title_style="bold green",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )
    table.add_column("Field", style="white", min_width=16)
    table.add_column("Value", style="bold", min_width=24)

    status_color = "green" if result.status in ("NEW", "FILLED") else "yellow"

    table.add_row("Order ID", str(result.order_id))
    table.add_row("Symbol", result.symbol)
    table.add_row("Side", result.side)
    table.add_row("Type", result.order_type)
    table.add_row(
        "Status", f"[{status_color}]{result.status}[/{status_color}]"
    )
    table.add_row("Quantity", result.quantity)
    table.add_row("Executed Qty", result.executed_qty)
    table.add_row("Price", result.price)
    table.add_row("Avg Price", result.avg_price)
    if result.time_in_force:
        table.add_row("Time in Force", result.time_in_force)

    console.print(table)
    console.print()


def _print_error(title: str, message: str) -> None:
    """Print an error panel."""
    console.print(
        Panel(
            f"[bold red]{message}[/bold red]",
            title=f"❌ {title}",
            border_style="red",
        )
    )


def _print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✅ {message}[/bold green]")


# ── CLI Commands ────────────────────────────────────────────────────────


@app.command()
def order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair (e.g., BTCUSDT)"),
    side: str = typer.Option(..., "--side", "-S", help="Order side: BUY or SELL"),
    order_type: str = typer.Option(
        ..., "--type", "-t", help="Order type: MARKET, LIMIT, or STOP_LIMIT"
    ),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[float] = typer.Option(
        None, "--price", "-p", help="Limit price (required for LIMIT/STOP_LIMIT)"
    ),
    stop_price: Optional[float] = typer.Option(
        None, "--stop-price", help="Stop trigger price (required for STOP_LIMIT)"
    ),
    time_in_force: str = typer.Option(
        "GTC", "--tif", help="Time in force: GTC, IOC, FOK"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview order without placing it"
    ),
) -> None:
    """Place an order on Binance Futures Testnet.

    \b
    Examples:
      # Market buy
      python -m trading_bot order -s BTCUSDT -S BUY -t MARKET -q 0.001

      # Limit sell
      python -m trading_bot order -s BTCUSDT -S SELL -t LIMIT -q 0.001 -p 95000

      # Stop-limit buy
      python -m trading_bot order -s BTCUSDT -S BUY -t STOP_LIMIT -q 0.001 -p 96000 --stop-price 95500
    """
    setup_logging()
    _print_banner()

    try:
        # Show order summary
        _print_order_summary(symbol, side, order_type, quantity, price, stop_price)

        if dry_run:
            console.print(
                Panel(
                    "[bold yellow]Dry run mode — order NOT placed.[/bold yellow]",
                    border_style="yellow",
                )
            )
            logger.info("Dry run — order skipped.")
            return

        # Load config and create client
        config = load_config()
        with BinanceClient(config.api_key, config.api_secret, config.base_url) as client:
            result = place_order(
                client=client,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                time_in_force=time_in_force,
            )

        _print_order_result(result)
        _print_success(f"Order {result.order_id} placed successfully!")

    except ValidationError as e:
        _print_error("Validation Error", str(e))
        logger.error("Validation error: %s", e)
        raise typer.Exit(code=1)

    except ConfigError as e:
        _print_error("Configuration Error", str(e))
        logger.error("Config error: %s", e)
        raise typer.Exit(code=1)

    except BinanceAPIError as e:
        _print_error("Binance API Error", str(e))
        logger.error("API error: %s", e)
        raise typer.Exit(code=1)

    except NetworkError as e:
        _print_error("Network Error", str(e))
        logger.error("Network error: %s", e)
        raise typer.Exit(code=1)

    except TradingBotError as e:
        _print_error("Error", str(e))
        logger.error("Trading bot error: %s", e)
        raise typer.Exit(code=1)


@app.command()
def interactive() -> None:
    """Launch interactive trading mode with guided prompts.

    Provides a menu-driven interface for placing orders with
    step-by-step input validation and confirmation.
    """
    setup_logging()
    _print_banner()

    try:
        config = load_config()
    except ConfigError as e:
        _print_error("Configuration Error", str(e))
        raise typer.Exit(code=1)

    console.print(
        "[dim]Tip: Type 'quit' or 'q' at any prompt to exit.[/dim]\n"
    )

    with BinanceClient(config.api_key, config.api_secret, config.base_url) as client:
        while True:
            try:
                console.print(
                    Panel(
                        "[bold]Select Order Type[/bold]\n\n"
                        "  [cyan]1[/cyan] — MARKET order\n"
                        "  [cyan]2[/cyan] — LIMIT order\n"
                        "  [cyan]3[/cyan] — STOP_LIMIT order [dim](bonus)[/dim]\n"
                        "  [cyan]q[/cyan] — Quit",
                        title="📊 Trading Menu",
                        border_style="cyan",
                    )
                )

                choice = Prompt.ask(
                    "[bold cyan]Choose[/bold cyan]",
                    choices=["1", "2", "3", "q", "quit"],
                    default="1",
                )

                if choice in ("q", "quit"):
                    console.print("[dim]Goodbye! 👋[/dim]")
                    break

                order_type_map = {"1": "MARKET", "2": "LIMIT", "3": "STOP_LIMIT"}
                order_type = order_type_map[choice]

                # ── Gather inputs ───────────────────────────────────
                symbol = Prompt.ask(
                    "[bold]Symbol[/bold] [dim](e.g., BTCUSDT)[/dim]"
                ).strip().upper()
                if symbol.lower() in ("q", "quit"):
                    break

                side = Prompt.ask(
                    "[bold]Side[/bold]",
                    choices=["BUY", "SELL", "buy", "sell"],
                ).strip().upper()

                quantity = FloatPrompt.ask("[bold]Quantity[/bold]")

                price = None
                stop_price = None

                if order_type in ("LIMIT", "STOP_LIMIT"):
                    price = FloatPrompt.ask("[bold]Price[/bold]")

                if order_type == "STOP_LIMIT":
                    stop_price = FloatPrompt.ask("[bold]Stop Price[/bold] [dim](trigger)[/dim]")

                # ── Show summary and confirm ────────────────────────
                console.print()
                _print_order_summary(symbol, side, order_type, quantity, price, stop_price)

                if not Confirm.ask("[bold yellow]Place this order?[/bold yellow]"):
                    console.print("[dim]Order cancelled.[/dim]\n")
                    continue

                # ── Place order ─────────────────────────────────────
                result = place_order(
                    client=client,
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    stop_price=stop_price,
                )

                _print_order_result(result)
                _print_success(f"Order {result.order_id} placed successfully!")
                console.print()

            except ValidationError as e:
                _print_error("Validation Error", str(e))
                console.print()

            except BinanceAPIError as e:
                _print_error("Binance API Error", str(e))
                console.print()

            except NetworkError as e:
                _print_error("Network Error", str(e))
                console.print()

            except KeyboardInterrupt:
                console.print("\n[dim]Interrupted. Goodbye! 👋[/dim]")
                break


# ── Entry guard ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
