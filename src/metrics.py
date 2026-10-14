"""Financial calculations: returns, risk, and the metrics used for grading."""

import math

import numpy as np
import pandas as pd

# The stock market is open about 252 days a year.
TRADING_DAYS_PER_YEAR = 252


def daily_returns(prices: pd.Series) -> pd.Series:
    """Percent change from one day to the next (0.01 means +1%)."""
    return prices.pct_change().dropna()


def annualized_return(prices: pd.Series) -> float:
    """Average yearly growth rate over the whole period (also called CAGR).

    Example: $100 -> $200 over 5 years is about 14.9% per year, not 20%,
    because growth compounds.
    """
    years = (prices.index[-1] - prices.index[0]).days / 365.25
    return (prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1


def annualized_volatility(prices: pd.Series) -> float:
    """How much the price jumps around, scaled to a yearly number.

    It is the standard deviation of daily returns times sqrt(252).
    Around 15-20% is typical for the S&P 500; 50%+ is a very bumpy stock.
    """
    return daily_returns(prices).std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def drawdown_series(prices: pd.Series) -> pd.Series:
    """For each day, how far the price is below its highest point so far."""
    running_peak = prices.cummax()
    return prices / running_peak - 1


def max_drawdown(prices: pd.Series) -> float:
    """The worst peak-to-bottom drop (-0.40 means it fell 40% at its worst)."""
    return drawdown_series(prices).min()


def beta(stock_prices: pd.Series, market_prices: pd.Series) -> float:
    """How much the stock tends to move when the market moves.

    1.0 = moves with the market, 2.0 = moves twice as much, 0.5 = half as much.
    Calculated as covariance(stock, market) / variance(market) of daily returns.
    """
    returns = pd.concat(
        [daily_returns(stock_prices), daily_returns(market_prices)], axis=1, join="inner"
    ).dropna()
    returns.columns = ["stock", "market"]
    return returns["stock"].cov(returns["market"]) / returns["market"].var()


def growth_of_10k(prices: pd.Series) -> pd.Series:
    """What $10,000 invested on the first day would be worth on each later day."""
    return prices / prices.iloc[0] * 10_000


def _clean_pe(value):
    """A P/E ratio only makes sense when the company has profits.

    Negative or missing earnings means the company is losing money, which we
    treat as the worst possible valuation (infinity).
    """
    if value is None:
        return None
    return math.inf if value <= 0 else value


def collect_metrics(info: dict, prices: pd.Series, market_prices: pd.Series) -> dict:
    """Gather every number used by the report card into one dictionary."""
    trailing_pe = _clean_pe(info.get("trailingPE"))
    if trailing_pe is None and (info.get("trailingEps") or 0) < 0:
        trailing_pe = math.inf  # Yahoo leaves P/E blank when earnings are negative

    return {
        # Growth and profitability come straight from Yahoo's company data.
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margin": info.get("profitMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        # Valuation
        "trailing_pe": trailing_pe,
        "forward_pe": _clean_pe(info.get("forwardPE")),
        "price_to_sales": info.get("priceToSalesTrailing12Months"),
        # Risk is calculated by us from the price history.
        "volatility": annualized_volatility(prices),
        "max_drawdown": max_drawdown(prices),
        "beta": beta(prices, market_prices),
        # Not graded, but shown for context.
        "annual_return": annualized_return(prices),
        "market_annual_return": annualized_return(market_prices),
    }
