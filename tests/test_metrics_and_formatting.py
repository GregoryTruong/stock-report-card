"""Checks collect_metrics and the display helpers on made-up data."""

import math

import numpy as np
import pandas as pd
import pytest

from src.grading import format_value, summary_for
from src.metrics import annualized_volatility, collect_metrics, growth_of_10k
from src.ui import format_large_number, format_price


def make_prices(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D"), dtype=float)


def wobbly_prices(seed, days=300):
    rng = np.random.default_rng(seed)
    return make_prices(100 * np.cumprod(1 + rng.normal(0, 0.01, days)))


def test_flat_price_has_no_volatility():
    assert annualized_volatility(make_prices([50.0] * 30)) == pytest.approx(0.0)


def test_growth_of_10k_starts_at_10k_and_tracks_price():
    growth = growth_of_10k(make_prices([20.0, 30.0, 10.0]))
    assert list(growth) == pytest.approx([10_000, 15_000, 5_000])


def test_collect_metrics_treats_losses_as_worst_pe():
    info = {"trailingPE": None, "trailingEps": -1.2, "forwardPE": -8.0}
    metrics = collect_metrics(info, wobbly_prices(1), wobbly_prices(2))
    assert math.isinf(metrics["trailing_pe"])
    assert math.isinf(metrics["forward_pe"])


def test_collect_metrics_passes_company_data_through():
    info = {"revenueGrowth": 0.12, "profitMargins": 0.25, "trailingPE": 22.5}
    metrics = collect_metrics(info, wobbly_prices(1), wobbly_prices(2))
    assert metrics["revenue_growth"] == 0.12
    assert metrics["profit_margin"] == 0.25
    assert metrics["trailing_pe"] == 22.5
    assert metrics["earnings_growth"] is None  # missing data stays missing


def test_stock_compared_to_itself_has_beta_of_one():
    prices = wobbly_prices(3)
    assert collect_metrics({}, prices, prices)["beta"] == pytest.approx(1.0)


def test_format_value():
    assert format_value(0.1234, "pct") == "12.3%"
    assert format_value(18.456, "ratio") == "18.46"
    assert format_value(None, "pct") == "No data"
    assert format_value(math.inf, "ratio") == "N/A (losing money)"


def test_summary_for_uses_score_bands():
    assert summary_for("Risk", 90) == "The price has been relatively steady."
    assert summary_for("Risk", 50) == "A normal amount of ups and downs."
    assert summary_for("Risk", 10).startswith("Big price swings")
    assert "doesn't have this data" in summary_for("Risk", None)


@pytest.mark.parametrize(
    ("value", "currency", "expected"),
    [
        (2.95e12, "USD", "$2.95T"),
        (48.2e9, "USD", "$48.20B"),
        (750e6, "CAD", "750.00M"),
        (12_345, "USD", "$12,345"),
        (None, "USD", "-"),
    ],
)
def test_format_large_number(value, currency, expected):
    assert format_large_number(value, currency) == expected


def test_format_price_shows_non_usd_currency():
    assert format_price(1234.5) == "$1,234.50"
    assert format_price(45.1, "CAD") == "45.10 CAD"


@pytest.mark.parametrize(("raw", "expected"), [("Infinity", math.inf), ("21.5", 21.5), ("abc", None),
                                                (float("nan"), None), (None, None), (-3, math.inf)])
def test_pe_values_from_yahoo_are_cleaned(raw, expected):
    metrics = collect_metrics({"forwardPE": raw}, wobbly_prices(1), wobbly_prices(2))
    assert metrics["forward_pe"] == expected
