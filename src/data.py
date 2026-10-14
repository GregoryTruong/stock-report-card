"""Downloads stock data from Yahoo Finance using the yfinance library."""

import pandas as pd
import yfinance as yf

# SPY is a fund that tracks the S&P 500, so we use it to represent "the market".
MARKET_TICKER = "SPY"

# Need at least ~3 months of trading days for the risk math to mean anything.
MIN_TRADING_DAYS = 60
# If the last trade is older than this, the stock has probably stopped trading.
MAX_DAYS_SINCE_LAST_TRADE = 14


def validate_prices(prices: pd.Series, ticker: str, today: pd.Timestamp | None = None) -> None:
    """Raise a clear error when there isn't enough usable price data.

    Catches stocks that stopped trading (buyouts, delistings) and brand-new
    listings, which would otherwise break the math with errors like division by zero.
    """
    today = today or pd.Timestamp.now()
    last_trade = prices.index[-1]
    if (today - last_trade).days > MAX_DAYS_SINCE_LAST_TRADE:
        raise ValueError(
            f"{ticker} hasn't traded since {last_trade:%b %d, %Y}. The company may have "
            "been bought out or removed from the stock exchange."
        )
    if len(prices) < MIN_TRADING_DAYS:
        raise ValueError(
            f"Only {len(prices)} days of price data for {ticker}. It may be too newly "
            f"listed to analyze (needs at least {MIN_TRADING_DAYS})."
        )


def get_price_history(ticker: str, period: str = "5y") -> pd.Series:
    """Return daily closing prices for a ticker, indexed by date.

    auto_adjust=True adjusts old prices for stock splits and dividends,
    so a 4-for-1 split doesn't look like a 75% crash.
    """
    history = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    if history.empty:
        raise ValueError(f"No price data found for '{ticker}'. Try searching by company name.")

    prices = history["Close"]
    # Remove timezone info so dates from different tickers line up cleanly.
    prices.index = prices.index.tz_localize(None)
    prices.name = ticker
    validate_prices(prices, ticker)
    return prices


def get_company_info(ticker: str) -> dict:
    """Return Yahoo Finance's company summary (name, sector, P/E, margins, etc.)."""
    return yf.Ticker(ticker).info or {}


def search_tickers(query: str, limit: int = 8) -> list[dict]:
    """Look up stocks by company name or ticker, e.g. "aritzia" -> ATZ.TO.

    Stocks outside the US have a suffix for their exchange (.TO = Toronto,
    .L = London), which is why searching by name is easier than guessing.
    """
    quotes = yf.Search(query, max_results=limit).quotes
    return [
        {
            "symbol": q["symbol"],
            "name": q.get("longname") or q.get("shortname") or q["symbol"],
            "exchange": q.get("exchDisp", ""),
        }
        for q in quotes
        if q.get("quoteType") in ("EQUITY", "ETF") and q.get("symbol")
    ]
