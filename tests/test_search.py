"""Checks how search results are ordered, without calling Yahoo Finance."""

import pytest

from src.data import rank_matches


def result(symbol, name="Some Company"):
    return {"symbol": symbol, "name": name, "exchange": "NASDAQ"}


def test_exact_ticker_match_goes_first():
    matches = [result("AAPU"), result("AAPL", "Apple Inc."), result("AAPB")]
    assert [m["symbol"] for m in rank_matches("aapl", matches)] == ["AAPL", "AAPU", "AAPB"]


def test_ticker_hidden_by_search_is_still_tried():
    # Yahoo's search leaves out stocks that stopped trading, like EA.
    ranked = rank_matches("EA", [result("EAT"), result("EARN")])
    assert ranked[0] == {"symbol": "EA", "name": "", "exchange": ""}
    assert len(ranked) == 3


def test_search_failure_still_tries_the_ticker():
    assert [m["symbol"] for m in rank_matches("ATZ.TO", [])] == ["ATZ.TO"]


def test_company_names_are_not_treated_as_tickers():
    matches = [result("ATZ.TO", "Aritzia Inc.")]
    assert rank_matches("aritzia inc", matches) == matches


def test_blank_query_adds_nothing():
    assert rank_matches("   ", []) == []


def test_company_name_search_puts_real_results_first():
    # "Aritzia" is the search box's own example; it used to open a fake ARITZIA ticker.
    ranked = rank_matches("Aritzia", [result("ATZ.TO", "Aritzia Inc.")])
    assert [m["symbol"] for m in ranked] == ["ATZ.TO", "ARITZIA"]
    assert rank_matches("tesla", [result("TSLA", "Tesla, Inc.")])[0]["symbol"] == "TSLA"


def test_lowercase_short_ticker_still_goes_first():
    assert rank_matches("ea", [result("EAT"), result("EARN")])[0]["symbol"] == "EA"


@pytest.mark.parametrize(
    "query,company", [("ford", "Ford Motor Company"), ("nike", "Nike, Inc."), ("visa", "Visa Inc.")]
)
def test_short_company_names_put_the_company_first(query, company):
    ranked = rank_matches(query, [result("F" if query == "ford" else "X", company), result(query.upper(), "Other Co")])
    assert ranked[0]["name"] == company
