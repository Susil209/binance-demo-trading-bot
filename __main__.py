"""Allow running the trading bot as a module: python -m trading_bot"""

import sys
import os

# Add the trading_bot directory to sys.path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import app

if __name__ == "__main__":
    app()
