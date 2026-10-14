"""Downloads stock data from Yahoo Finance using the yfinance library."""

import pandas as pd
import yfinance as yf

# SPY is a fund that tracks the S&P 500, so we use it to represent "the market".
MARKET_TICKER = "SPY"


def get_price_history(ticker: str, period: str = "5y") -> pd.Series:
    """Return daily closing prices for a ticker, indexed by date.

    auto_adjust=True adjusts old prices for stock splits and dividends,
    so a 4-for-1 split doesn't look like a 75% crash.
    """
    history = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if history.empty:
        raise ValueError(f"No price data found for '{ticker}'. Check the ticker symbol.")

    prices = history["Close"]
    # Remove timezone info so dates from different tickers line up cleanly.
    prices.index = prices.index.tz_localize(None)
    prices.name = ticker
    return prices


def get_company_info(ticker: str) -> dict:
    """Return Yahoo Finance's company summary (name, sector, P/E, margins, etc.)."""
    return yf.Ticker(ticker).info or {}
