"""Checks the math on small made-up price series where we know the right answer."""

import math

import pandas as pd
import pytest

from src.grading import build_report_card, letter_grade, score_metric
from src.metrics import annualized_return, beta, max_drawdown


def make_prices(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D"), dtype=float)


def test_max_drawdown_finds_worst_drop():
    # Peaks at 120, falls to 60 (a 50% drop), then recovers.
    prices = make_prices([100, 120, 90, 60, 110, 130])
    assert max_drawdown(prices) == pytest.approx(-0.5)


def test_annualized_return_doubling_over_one_year():
    start = pd.Timestamp("2020-01-01")
    prices = pd.Series([100.0, 200.0], index=[start, start + pd.Timedelta(days=365.25)])
    assert annualized_return(prices) == pytest.approx(1.0, rel=0.01)


def test_beta_of_stock_that_moves_twice_the_market():
    market_returns = [0.01, -0.02, 0.015, -0.005, 0.02]
    market, stock = [100.0], [100.0]
    for r in market_returns:
        market.append(market[-1] * (1 + r))
        stock.append(stock[-1] * (1 + 2 * r))
    assert beta(make_prices(stock), make_prices(market)) == pytest.approx(2.0)


def test_score_metric_scales_and_clamps():
    assert score_metric(0.125, 0.0, 0.25) == pytest.approx(50)
    assert score_metric(1.0, 0.0, 0.25) == 100     # above "best" is capped
    assert score_metric(25, 40, 12) > 50          # lower P/E scores higher
    assert score_metric(math.inf, 40, 12) == 0    # losing money = worst valuation
    assert score_metric(None, 0, 1) is None


def test_letter_grades():
    assert [letter_grade(s) for s in (90, 70, 55, 40, 10, None)] == ["A", "B", "C", "D", "F", "N/A"]


def test_report_card_handles_missing_data():
    card = build_report_card({"volatility": 0.15, "max_drawdown": -0.15, "beta": 0.8})
    assert card["categories"]["Risk"]["grade"] == "A"
    assert card["categories"]["Growth"]["grade"] == "N/A"
    assert card["overall_grade"] == "A"  # only categories with data count
