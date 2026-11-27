"""Checks the HTML and chart helpers without running the app."""

import pandas as pd

from src.grading import build_report_card
from src.ui import THEMES, _rgba, grade_chip, radar_chart, scorecard_html, top_three_html


def test_rgba_converts_hex():
    assert _rgba("#34D399", 0.5) == "rgba(52, 211, 153, 0.5)"


def test_grade_chip_uses_the_current_themes_grade_color():
    from src import ui

    for mode in ("dark", "light"):
        ui.set_theme(mode)
        try:
            assert THEMES[mode]["GRADE_COLORS"]["A"] in grade_chip("A")
            assert THEMES[mode]["GRADE_COLORS"]["N/A"] in grade_chip("something odd")
        finally:
            ui.set_theme("dark")


def test_class_rank_skips_stocks_without_an_overall_grade():
    ranked = pd.DataFrame([
        {"Ticker": "AAA", "Company": "Alpha", "Overall": "A", "Score": 90.0},
        {"Ticker": "FUND", "Company": "Fund", "Overall": "N/A", "Score": None},
    ])
    page = top_three_html(ranked)
    assert "AAA" in page and "FUND" not in page and "nan" not in page  # unknown grades fall back to gray


def test_scorecard_shows_verdict_and_every_category():
    card = build_report_card({"volatility": 0.15, "max_drawdown": -0.15, "beta": 0.8,
                              "profit_margin": 0.3, "return_on_equity": 0.4})
    page = scorecard_html(card)
    assert "Top of the class" in page
    for name in ("Growth", "Profitability", "Valuation", "Risk"):
        assert name in page


def _ranked():
    return pd.DataFrame([
        {"Ticker": "AAA", "Company": "Alpha", "Overall": "A", "Score": 90.0},
        {"Ticker": "BBB", "Company": "Beta", "Overall": "B", "Score": 70.0},
        {"Ticker": "CCC", "Company": "Gamma", "Overall": "C", "Score": 55.0},
        {"Ticker": "DDD", "Company": "Delta", "Overall": "D", "Score": 40.0},
    ])


def test_class_rank_lists_the_top_three_in_order():
    page = top_three_html(_ranked())
    assert page.index("AAA") < page.index("BBB") < page.index("CCC")
    assert "DDD" not in page


def test_radar_skips_stocks_with_missing_categories():
    table = pd.DataFrame([
        {"Ticker": "FULL", "Growth score": 50, "Risk score": 70},
        {"Ticker": "GAPS", "Growth score": None, "Risk score": 70},
    ])
    fig = radar_chart(table, ["Growth", "Risk"])
    assert [trace.name for trace in fig.data] == ["FULL"]


def test_light_theme_swaps_colors_only_for_this_thread():
    import threading

    from src import ui

    seen = {}

    def other_visitor():
        seen["other"] = ui.grade_color("A")  # a new thread starts on the dark palette

    ui.set_theme("light")
    try:
        assert ui.grade_color("A") == ui.THEMES["light"]["GRADE_COLORS"]["A"]
        assert ui.THEMES["light"]["BG"] in ui.css()
        thread = threading.Thread(target=other_visitor)
        thread.start()
        thread.join()
        assert seen["other"] == ui.THEMES["dark"]["GRADE_COLORS"]["A"]
    finally:
        ui.set_theme("dark")


def test_no_emoji_icon_sets_or_decorative_effects():
    """Guards the look G2 asked for: no emoji, no Lucide icons, no glows, gradients or glass."""
    import re
    from pathlib import Path

    emoji = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF]")
    banned = ("lucide", ":material/", "box-shadow", "text-shadow", "drop-shadow", "linear-gradient",
              "radial-gradient", "backdrop-filter", ":hover", "Space Grotesk", "Geist", "\u2014")
    for path in ("app.py", "src/ui.py", ".streamlit/config.toml"):
        text = Path(path).read_text(encoding="utf-8")
        assert not emoji.search(text), f"emoji found in {path}"
        for word in banned:
            assert word not in text, f"{word!r} found in {path}"
        assert not re.search(r"\bInter\b", text), f"the Inter font is used in {path}"
