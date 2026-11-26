"""Checks the HTML and chart helpers without running the app."""

import pandas as pd

from src.grading import build_report_card
from src.ui import _rgba, grade_chip, podium_html, radar_chart, scorecard_html


def test_rgba_converts_hex():
    assert _rgba("#34D399", 0.5) == "rgba(52, 211, 153, 0.5)"


def test_grade_chip_uses_grade_color():
    assert "#34D399" in grade_chip("A")
    assert "#94A3B8" in grade_chip("something odd")  # unknown grades fall back to gray


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


def test_podium_puts_winner_in_the_middle_and_shows_top_three():
    page = podium_html(_ranked())
    assert page.index("BBB") < page.index("AAA") < page.index("CCC")
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


def test_app_uses_line_icons_not_emoji():
    import re
    from pathlib import Path

    from src.ui import CATEGORY_ICONS, ICONS, icon

    emoji = re.compile("[\U0001F000-\U0001FAFF☀-➿]")
    for path in ("app.py", "src/ui.py"):
        assert not emoji.search(Path(path).read_text(encoding="utf-8")), f"emoji found in {path}"
    assert set(CATEGORY_ICONS.values()) <= set(ICONS)
    assert 'class="rc-icon rc-i-shield"' in icon("shield")
