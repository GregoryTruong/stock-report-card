"""Runs the real app.py end to end with made-up market data and checks nothing crashes.

These tests click through every page the way a visitor would: different kinds of
stocks (normal, money-losing, a fund, non-US, delisted, unknown), the Compare page
and the Methodology page. Yahoo Finance is replaced with fake data, so they run
offline and give the same result every time.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.data as data

APP = str(Path(__file__).resolve().parents[1] / "app.py")
TODAY = pd.Timestamp.now().normalize()

COMPANIES = {
    "AAPL": {"longName": "Apple Inc.", "shortName": "Apple", "sector": "Technology",
             "industry": "Consumer Electronics", "currency": "USD", "marketCap": 3.4e12,
             "revenueGrowth": 0.06, "earningsGrowth": 0.1, "profitMargins": 0.25,
             "returnOnEquity": 1.5, "trailingPE": 33.0, "forwardPE": 29.0,
             "priceToSalesTrailing12Months": 8.7},
    # Losing money: Yahoo leaves trailingPE blank and EPS is negative.
    "LOSS": {"longName": "Losing Money Corp", "sector": "Consumer Cyclical", "currency": "USD",
             "marketCap": 2e9, "revenueGrowth": -0.2, "earningsGrowth": -0.9, "profitMargins": -0.3,
             "returnOnEquity": -0.4, "trailingPE": None, "trailingEps": -2.1, "forwardPE": -15.0},
    # A fund: no sector, no company fundamentals at all.
    "SPYX": {"longName": "Some Index Fund", "currency": "USD"},
    # Non-US stock priced in Canadian dollars.
    "ATZ.TO": {"longName": "Aritzia Inc.", "sector": "Consumer Cyclical", "industry": "Apparel Retail",
               "currency": "CAD", "marketCap": 6e9, "revenueGrowth": 0.1, "profitMargins": 0.05,
               "trailingPE": 45.0},
    # Yahoo sometimes returns keys with empty values.
    "BLANK": {"longName": None, "shortName": None, "currency": None, "sector": None},
}


def fake_history(ticker, period="5y"):
    days = {"1y": 252, "3y": 756, "5y": 1260, "10y": 2520}[period]
    if ticker == "NOPE":
        raise ValueError(f"No price data found for '{ticker}'. Try searching by company name.")
    end = TODAY - pd.Timedelta(days=200) if ticker == "GONE" else TODAY  # GONE stopped trading
    rng = np.random.default_rng(sum(map(ord, ticker)))
    prices = pd.Series(100 * np.cumprod(1 + rng.normal(0.0004, 0.015, days)),
                       index=pd.bdate_range(end=end, periods=days), name=ticker)
    data.validate_prices(prices, ticker)
    return prices


@pytest.fixture(autouse=True)
def fake_yahoo(monkeypatch):
    monkeypatch.setattr(data, "get_price_history", fake_history)
    monkeypatch.setattr(data, "get_company_info", lambda t: dict(COMPANIES.get(t, {})))
    monkeypatch.setattr(data, "search_tickers", lambda q, limit=8: [])
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def run_app(**query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    for key, value in query.items():
        at.query_params[key] = value
    return at.run()


def errors(at):
    return [e.value for e in at.error]


@pytest.mark.parametrize("ticker", ["AAPL", "LOSS", "SPYX", "ATZ.TO", "BLANK"])
@pytest.mark.parametrize("period", ["1Y", "5Y", "10Y"])
def test_report_card_loads(ticker, period):
    at = run_app(q=ticker, period=period)
    assert not at.exception, at.exception
    assert not errors(at)
    assert at.query_params["q"] == [ticker] or at.query_params["q"] == ticker


def test_delisted_stock_shows_a_clear_message():
    at = run_app(q="GONE")
    assert not at.exception
    assert any("hasn't traded since" in e for e in errors(at))


def test_unknown_ticker_shows_a_clear_message():
    at = run_app(q="NOPE")
    assert not at.exception
    assert any("No price data found" in e for e in errors(at))


def test_typing_a_new_search_reloads_the_card():
    at = run_app(q="AAPL")
    at.text_input(key="query").set_value("LOSS").run()
    assert not at.exception
    assert not errors(at)


def test_compare_page_ranks_stocks_and_skips_bad_ones():
    at = run_app(page="Compare")
    at.text_input(key="compare_input").set_value("AAPL, LOSS, SPYX, ATZ.TO, GONE, NOPE").run()
    assert not at.exception
    skipped = " ".join(w.value for w in at.warning)
    assert "GONE" in skipped and "NOPE" in skipped
    table = at.dataframe[0].value
    assert set(table["Ticker"]) == {"AAPL", "LOSS", "SPYX", "ATZ.TO"}
    assert list(table["Score"]) == sorted(table["Score"], reverse=True)  # best first
    assert "SPY" not in list(table["Ticker"])  # the market benchmark isn't ranked


def test_compare_page_with_one_stock():
    at = run_app(page="Compare")
    at.text_input(key="compare_input").set_value("AAPL").run()
    assert not at.exception


def test_methodology_page():
    at = run_app(page="Methodology")
    assert not at.exception
    assert any("How the grading works" in h.value for h in at.header)
