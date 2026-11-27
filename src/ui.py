"""Visual building blocks: the two themes, the report card widgets and chart styling.

The look is a printed school report card: warm paper (or graphite at night), ink
text, a serif for headings, thin rules instead of shadows, and square corners.
Color is only used where it means something: the grade, the stock and the market.
"""

import html
import threading

import pandas as pd
import plotly.graph_objects as go

# Two palettes, one per theme. Grades run from green (A) to brick red (F), muted so
# the page reads like ink on paper rather than a neon dashboard.
THEMES = {
    "dark": {
        "GRADE_COLORS": {"A": "#86B98F", "B": "#AFC285", "C": "#D8B56A", "D": "#DB9970",
                         "F": "#E0887E", "N/A": "#8E9196"},
        "STOCK_COLOR": "#8FB3D9", "MARKET_COLOR": "#7D8187",
        "GAIN_COLOR": "#86B98F", "LOSS_COLOR": "#E0887E",
        "TEXT": "#E9E5DB", "MUTED": "#9C988F",
        "BG": "#17191C", "PANEL": "#1E2125", "SIDEBAR": "#1B1D20",
        "BORDER": "#353940", "TRACK": "#2B2F34", "GRID": "#2B2F34",
        "SERIES": ["#8FB3D9", "#E0887E", "#AFC285", "#D8B56A", "#B9B4A9", "#7FB7B3", "#C9A27E", "#9EA3C0"],
    },
    "light": {
        "GRADE_COLORS": {"A": "#2E6B3F", "B": "#58743A", "C": "#94701E", "D": "#A55A2C",
                         "F": "#A3332B", "N/A": "#73757A"},
        "STOCK_COLOR": "#1F4E79", "MARKET_COLOR": "#8C8F94",
        "GAIN_COLOR": "#2E6B3F", "LOSS_COLOR": "#A3332B",
        "TEXT": "#1C1E21", "MUTED": "#5F6166",
        "BG": "#F3F0E8", "PANEL": "#FAF8F3", "SIDEBAR": "#ECE8DE",
        "BORDER": "#D3CCBE", "TRACK": "#E4DED2", "GRID": "#E2DCD0",
        "SERIES": ["#1F4E79", "#A3332B", "#58743A", "#94701E", "#4B5563", "#2F6F73", "#7A4E2D", "#5A5F86"],
    },
}
# One short verdict per overall grade, like the line a teacher writes at the bottom.
VERDICTS = {
    "A": "Top of the class",
    "B": "Strong all-rounder",
    "C": "Middle of the pack",
    "D": "Needs work",
    "F": "Struggling",
    "N/A": "Not enough data",
}


class _Palette(threading.local):
    """The active theme's colors, e.g. T.TEXT.

    Streamlit runs each visitor's session in its own thread, so keeping the
    palette per thread means one visitor's light mode never leaks into
    another visitor's dark mode.
    """

    def __init__(self):
        self.__dict__.update(THEMES["dark"])


T = _Palette()


def set_theme(mode: str) -> None:
    """Switch to the "dark" or "light" palette. The app calls this before drawing anything."""
    T.__dict__.update(THEMES.get(mode, THEMES["dark"]))


SERIF = "'Source Serif 4', Georgia, serif"
MONO = "'IBM Plex Mono', ui-monospace, monospace"
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600;8..60,700"
             "&family=IBM+Plex+Mono:wght@400;500&display=swap")


def _rgba(hex_color: str, alpha: float) -> str:
    """'#34D399', 0.15 -> 'rgba(52, 211, 153, 0.15)'."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def grade_color(grade: str) -> str:
    return T.GRADE_COLORS.get(grade, T.GRADE_COLORS["N/A"])


def css() -> str:
    """The page stylesheet, built from the current theme's colors."""
    return f"""
<style>
@import url("{FONTS_URL}");
.stApp {{ background: {T.BG}; }}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ font-family: {SERIF} !important; font-weight: 700 !important; letter-spacing: -0.01em; }}

.rc-panel {{ background: {T.PANEL}; border: 1px solid {T.BORDER}; border-radius: 4px; }}
.rc-label {{ font-size: .74rem; color: {T.MUTED}; text-transform: uppercase; letter-spacing: .09em; }}
.rc-num {{ font-family: {MONO}; font-variant-numeric: tabular-nums; }}

/* Masthead */
.rc-hero {{ padding: 4px 0 18px; border-bottom: 1px solid {T.BORDER}; margin-bottom: 18px; }}
.rc-hero h1 {{ font-size: clamp(1.9rem, 4vw, 2.7rem); line-height: 1.1; margin: 6px 0 10px; padding: 0;
  color: {T.TEXT}; }}
.rc-hero p {{ color: {T.MUTED}; font-size: 1.02rem; max-width: 640px; margin: 0; line-height: 1.55; }}

/* Company header */
.rc-header {{ display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap;
  gap: 12px 24px; margin: 10px 0 14px; padding-bottom: 14px; border-bottom: 1px solid {T.BORDER}; }}
.rc-name {{ font-family: {SERIF}; font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 700;
  line-height: 1.15; color: {T.TEXT}; }}
.rc-sub {{ margin-top: 6px; font-size: .9rem; color: {T.MUTED}; }}
.rc-sub .tk {{ font-family: {MONO}; color: {T.TEXT}; font-weight: 500; margin-right: 10px; }}
.rc-price {{ font-family: {MONO}; font-size: clamp(1.5rem, 3vw, 2rem); font-weight: 500;
  text-align: right; color: {T.TEXT}; }}
.rc-change {{ font-family: {MONO}; font-size: .88rem; text-align: right; margin-top: 2px; }}

/* Key numbers: one strip split by thin rules */
.rc-stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 18px; }}
.rc-stat {{ padding: 14px 16px; border-left: 1px solid {T.BORDER}; }}
.rc-stat:first-child {{ border-left: 0; }}
.rc-stat .v {{ font-family: {MONO}; font-size: 1.35rem; font-weight: 500; color: {T.TEXT}; margin-top: 6px; }}
.rc-stat .d {{ font-family: {MONO}; font-size: .78rem; margin-top: 3px; }}

/* The report card itself */
.rc-sheet {{ display: grid; grid-template-columns: 220px 1fr; margin: 0 0 14px; }}
.rc-overall {{ padding: 22px 20px; border-right: 1px solid {T.BORDER}; text-align: center; }}
.rc-overall .big {{ font-family: {SERIF}; font-size: 4.6rem; font-weight: 700; line-height: 1; margin: 10px 0 8px; }}
.rc-overall .verdict {{ font-family: {SERIF}; font-size: 1.1rem; font-weight: 600; color: {T.TEXT}; }}
.rc-overall .score {{ font-family: {MONO}; font-size: .85rem; color: {T.MUTED}; margin-top: 4px; }}
table.rc-subjects {{ width: 100%; border-collapse: collapse; }}
table.rc-subjects th {{ text-align: left; font-weight: 500; padding: 12px 16px 8px;
  border-bottom: 1px solid {T.BORDER}; }}
table.rc-subjects td {{ padding: 13px 16px; border-bottom: 1px solid {T.TRACK}; color: {T.TEXT};
  vertical-align: middle; }}
table.rc-subjects tr:last-child td {{ border-bottom: 0; }}
table.rc-subjects td.subject {{ font-family: {SERIF}; font-weight: 600; font-size: 1.05rem; white-space: nowrap; }}
table.rc-subjects td.comment {{ color: {T.MUTED}; font-size: .92rem; }}
.rc-score {{ display: flex; align-items: center; gap: 10px; min-width: 120px; }}
.rc-score .bar {{ flex: 1; height: 4px; background: {T.TRACK}; }}
.rc-score .bar span {{ display: block; height: 100%; }}
.rc-score b {{ font-family: {MONO}; font-weight: 500; width: 2.2em; text-align: right; }}

.rc-chip {{ display: inline-flex; align-items: center; justify-content: center; min-width: 32px; height: 32px;
  padding: 0 5px; box-sizing: border-box; white-space: nowrap;
  border-radius: 3px; font-family: {SERIF}; font-weight: 700; font-size: 1.1rem; border: 1px solid; }}

/* Compare: class rank */
.rc-rank {{ margin: 6px 0 18px; }}
.rc-rank .row {{ display: grid; grid-template-columns: 34px 90px 1fr auto 96px; align-items: center; gap: 12px;
  padding: 12px 16px; border-top: 1px solid {T.TRACK}; }}
.rc-rank .row:first-child {{ border-top: 0; }}
.rc-rank .pos {{ font-family: {SERIF}; font-weight: 700; font-size: 1.2rem; color: {T.MUTED}; }}
.rc-rank .tk {{ font-family: {MONO}; font-weight: 500; color: {T.TEXT}; }}
.rc-rank .co {{ color: {T.MUTED}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.rc-rank .sc {{ font-family: {MONO}; color: {T.MUTED}; text-align: right; white-space: nowrap; }}

/* Plain tables (methodology) */
table.rc-table {{ width: 100%; border-collapse: collapse; }}
table.rc-table th {{ text-align: left; color: {T.MUTED}; font-weight: 500; font-size: .8rem;
  padding: 8px 12px; border-bottom: 1px solid {T.BORDER}; }}
table.rc-table td {{ padding: 10px 12px; border-bottom: 1px solid {T.TRACK}; color: {T.TEXT}; }}

/* Loading placeholder, shaped like the page that is about to appear */
.rc-skel {{ background: {T.TRACK}; border-radius: 2px; animation: rc-wait 1.4s ease-in-out infinite; }}
@keyframes rc-wait {{ 50% {{ opacity: .45; }} }}

/* Streamlit widgets, tuned to the theme */
[data-testid="stButtonGroup"] button {{ border-radius: 4px !important; }}
[data-testid="stSidebar"] {{ background: {T.SIDEBAR}; border-right: 1px solid {T.BORDER}; }}
[data-testid="stExpander"] details {{ background: {T.PANEL}; border-radius: 4px; border-color: {T.BORDER}; }}
[data-testid="stPlotlyChart"] {{ background: {T.PANEL}; border: 1px solid {T.BORDER}; border-radius: 4px;
  padding: 8px; }}

@media (max-width: 900px) {{
  .rc-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .rc-stat:nth-child(3) {{ border-left: 0; }}
  .rc-stat:nth-child(n+3) {{ border-top: 1px solid {T.BORDER}; }}
}}
@media (max-width: 640px) {{
  .rc-sheet {{ grid-template-columns: 1fr; }}
  .rc-overall {{ border-right: 0; border-bottom: 1px solid {T.BORDER}; }}
  table.rc-subjects th.comment, table.rc-subjects td.comment {{ display: none; }}
  .rc-rank .row {{ grid-template-columns: 26px 70px 1fr auto; }}
  .rc-rank .co {{ display: none; }}
  .rc-price, .rc-change {{ text-align: left; }}
}}
@media (prefers-reduced-motion: reduce) {{
  .rc-skel {{ animation: none; }}
}}
</style>
"""


def grade_chip(grade: str) -> str:
    color = grade_color(grade)
    size = "font-size:.8rem;" if len(str(grade)) > 1 else ""  # "N/A" needs to fit the box
    return (f'<span class="rc-chip" style="{size}color:{color};border-color:{_rgba(color, .55)};'
            f'background:{_rgba(color, .08)}">{html.escape(str(grade))}</span>')


def hero_html() -> str:
    return """
    <div class="rc-hero">
      <h1>A report card for any stock.</h1>
      <p>Graded A to F in growth, profitability, valuation and risk.</p>
    </div>"""


def format_price(value, currency="USD") -> str:
    """$12.34 for US dollars, otherwise 12.34 CAD (or whatever the currency is)."""
    return f"${value:,.2f}" if currency == "USD" else f"{value:,.2f} {html.escape(str(currency))}"


def header_html(name, ticker, subtitle, price, change, currency="USD") -> str:
    color = T.GAIN_COLOR if change >= 0 else T.LOSS_COLOR
    sign = "+" if change >= 0 else "−"  # a real minus sign, not a hyphen
    return f"""
    <div class="rc-header">
      <div>
        <div class="rc-name">{html.escape(name)}</div>
        <div class="rc-sub"><span class="tk">{html.escape(ticker)}</span>{html.escape(subtitle)}</div>
      </div>
      <div>
        <div class="rc-price">{format_price(price, currency)}</div>
        <div class="rc-change" style="color:{color}">{sign}{abs(change):.2%} today</div>
      </div>
    </div>"""


def stats_html(stats) -> str:
    """One strip of key numbers. Each stat is (label, value, note or None, note is good news)."""
    cells = ""
    for label, value, delta, good in stats:
        delta_html = ""
        if delta:
            color = T.GAIN_COLOR if good else T.LOSS_COLOR
            delta_html = f'<div class="d" style="color:{color}">{html.escape(delta)}</div>'
        cells += f"""
        <div class="rc-stat">
          <div class="rc-label">{html.escape(label)}</div><div class="v">{html.escape(value)}</div>{delta_html}
        </div>"""
    return f'<div class="rc-panel rc-stats">{cells}</div>'


def scorecard_html(card: dict) -> str:
    """The overall grade on the left, and one row per subject like a school report card."""
    overall = card["overall_score"]
    grade = card["overall_grade"]
    overall_text = f"{overall:.0f} / 100" if overall is not None else "No overall score"
    rows = ""
    for name, category in card["categories"].items():
        score = category["score"]
        color = grade_color(category["grade"])
        width = 0 if score is None else score
        score_text = "-" if score is None else f"{score:.0f}"
        rows += f"""
        <tr>
          <td class="subject">{name}</td>
          <td>{grade_chip(category["grade"])}</td>
          <td><div class="rc-score"><div class="bar"><span style="width:{width}%;background:{color}"></span></div>
              <b>{score_text}</b></div></td>
          <td class="comment">{html.escape(category["summary"])}</td>
        </tr>"""
    return f"""
    <div class="rc-panel rc-sheet">
      <div class="rc-overall">
        <div class="rc-label">Overall</div>
        <div class="big" style="color:{grade_color(grade)}">{grade}</div>
        <div class="verdict">{VERDICTS.get(grade, "")}</div>
        <div class="score">{overall_text}</div>
      </div>
      <table class="rc-subjects">
        <tr><th class="rc-label">Subject</th><th class="rc-label">Grade</th><th class="rc-label">Score</th>
            <th class="rc-label comment">Comment</th></tr>
        {rows}
      </table>
    </div>"""


def skeleton_html() -> str:
    """Gray blocks in the shape of a report card, shown while the data downloads."""
    def block(width, height, extra=""):
        return f'<div class="rc-skel" style="width:{width};height:{height}px;{extra}"></div>'

    stats = "".join(f'<div class="rc-stat">{block("50%", 10)}{block("70%", 22, "margin-top:10px")}</div>'
                    for _ in range(4))
    rows = "".join(f'<div style="display:flex;gap:16px;padding:14px 16px">{block("22%", 16)}'
                   f'{block("8%", 16)}{block("60%", 16)}</div>' for _ in range(4))
    return f"""
    <div aria-busy="true" aria-label="Loading">
      <div class="rc-header"><div style="flex:1">{block("45%", 30)}{block("30%", 12, "margin-top:10px")}</div>
        {block("120px", 30)}</div>
      <div class="rc-panel rc-stats">{stats}</div>
      <div class="rc-panel rc-sheet"><div class="rc-overall">{block("60%", 80, "margin:10px auto")}</div>
        <div>{rows}</div></div>
    </div>"""


def top_three_html(ranked: pd.DataFrame) -> str:
    """The top three stocks as a short class ranking."""
    top = ranked[ranked["Score"].notna()].head(3).to_dict("records")
    if not top:
        return ""
    rows = "".join(f"""
        <div class="row">
          <div class="pos">{rank}</div>
          <div class="tk">{html.escape(row["Ticker"])}</div>
          <div class="co">{html.escape(str(row["Company"]))}</div>
          <div>{grade_chip(row["Overall"])}</div>
          <div class="sc">{row["Score"]:.0f} / 100</div>
        </div>""" for rank, row in enumerate(top, start=1))
    return f'<div class="rc-label">Class rank</div><div class="rc-panel rc-rank">{rows}</div>'


def grade_table_html() -> str:
    """The grade-to-score table on the Methodology page."""
    rows = "".join(
        f"<tr><td>{grade_chip(g)}</td><td>{s}</td><td>{VERDICTS[g]}</td></tr>"
        for g, s in (("A", "80 and up"), ("B", "65 to 79"), ("C", "50 to 64"),
                     ("D", "35 to 49"), ("F", "Under 35"))
    )
    return (f'<div class="rc-panel"><table class="rc-table"><tr><th>Grade</th><th>Score</th>'
            f'<th>Verdict</th></tr>{rows}</table></div>')


def grade_cell_style(grade) -> str:
    """Used to color grade cells in the comparison table."""
    color = grade_color(grade)
    return f"color: {color}; font-weight: 600"


def format_large_number(value, currency="USD") -> str:
    if not value:
        return "-"
    for limit, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= limit:
            number = f"{value / limit:.2f}{suffix}"
            break
    else:
        number = f"{value:,.0f}"
    return f"${number}" if currency == "USD" else number


def _style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 36, "b": 8},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "IBM Plex Sans, sans-serif", "size": 13, "color": T.TEXT},
        hovermode="x unified",
        hoverlabel={"bgcolor": T.PANEL, "bordercolor": T.BORDER, "font": {"color": T.TEXT}},
        legend={"orientation": "h", "y": 1.1, "x": 0, "bgcolor": "rgba(0,0,0,0)"},
    )
    fig.update_xaxes(showgrid=False, linecolor=T.BORDER, tickfont={"color": T.MUTED})
    fig.update_yaxes(gridcolor=T.GRID, zeroline=False, tickfont={"color": T.MUTED})
    return fig


def growth_chart(stock: pd.Series, market: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=market.index, y=market, name="S&P 500 (SPY)",
                    line={"color": T.MARKET_COLOR, "width": 1.5, "dash": "dot"})
    fig.add_scatter(x=stock.index, y=stock, name=ticker, line={"color": T.STOCK_COLOR, "width": 2})
    # A small dot where each line ends, so the final values are easy to find.
    for series, color in ((market, T.MARKET_COLOR), (stock, T.STOCK_COLOR)):
        fig.add_scatter(x=[series.index[-1]], y=[series.iloc[-1]], mode="markers", showlegend=False,
                        marker={"size": 7, "color": color}, hoverinfo="skip")
    fig.add_hline(y=10_000, line={"color": T.MUTED, "width": 1, "dash": "dash"})
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", rangemode="tozero")
    fig.update_traces(hovertemplate="$%{y:,.0f}", selector={"mode": "lines"})
    return _style(fig)


def drawdown_chart(drawdown: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=drawdown.index, y=drawdown, name="Below peak", mode="lines",
                    line={"color": T.LOSS_COLOR, "width": 1.5}, fill="tozeroy",
                    fillcolor=_rgba(T.LOSS_COLOR, .14), hovertemplate="%{y:.1%}")
    worst = drawdown.idxmin()
    fig.add_annotation(x=worst, y=drawdown.min(), text=f"Worst: {drawdown.min():.0%}", showarrow=True,
                       arrowcolor=T.LOSS_COLOR, font={"color": T.LOSS_COLOR, "family": "IBM Plex Mono"},
                       ay=30, bgcolor=T.PANEL, bordercolor=_rgba(T.LOSS_COLOR, .4))
    fig.update_yaxes(tickformat=".0%")
    fig = _style(fig, height=300)
    fig.update_layout(showlegend=False)
    return fig


def risk_return_chart(table: pd.DataFrame) -> go.Figure:
    """Classic finance chart: yearly return (up) vs. volatility (right).

    Up and to the left is the best place to be: high return, low risk.
    Each stock's dot is colored by its overall grade.
    """
    is_market = table["Ticker"] == "SPY"
    stocks, market = table[~is_market], table[is_market]
    fig = go.Figure()
    fig.add_scatter(
        x=stocks["Volatility"], y=stocks["Yearly return"], mode="markers+text", cliponaxis=False,
        text=stocks["Ticker"], textposition="top center", textfont={"family": "IBM Plex Mono", "color": T.TEXT},
        marker={"size": 13, "color": [grade_color(g) for g in stocks["Overall"]],
                "line": {"width": 1, "color": T.PANEL}},
        customdata=stocks["Overall"],
        hovertemplate="%{text} · grade %{customdata}<br>Return %{y:.1%}<br>Volatility %{x:.1%}<extra></extra>",
    )
    fig.add_scatter(
        x=market["Volatility"], y=market["Yearly return"], mode="markers+text", text=["S&P 500"],
        textposition="bottom center", textfont={"color": T.MUTED},
        marker={"size": 14, "color": T.MARKET_COLOR, "symbol": "diamond"},
        hovertemplate="S&P 500<br>Return %{y:.1%}<br>Volatility %{x:.1%}<extra></extra>",
    )
    if len(market):
        fig.add_vline(x=market["Volatility"].iloc[0], line={"color": T.GRID, "dash": "dot"})
        fig.add_hline(y=market["Yearly return"].iloc[0], line={"color": T.GRID, "dash": "dot"})
    fig.update_xaxes(title="Volatility (yearly)", tickformat=".0%")
    fig.update_yaxes(title="Average yearly return", tickformat=".0%")
    fig = _style(fig, height=440)
    fig.update_layout(hovermode="closest", showlegend=False)
    return fig


def radar_chart(table: pd.DataFrame, categories) -> go.Figure:
    """One outline per stock across the four category scores. Bigger shape = better stock.

    Stocks missing a category (common for funds) are left out, since a gap would
    look like a score of zero.
    """
    palette = T.SERIES
    axes = [*categories, categories[0]]  # repeat the first point to close the shape
    fig = go.Figure()
    for i, row in enumerate(table.to_dict("records")):
        color = palette[i % len(palette)]
        scores = [row.get(f"{c} score") for c in axes]
        if any(score is None or score != score for score in scores):  # None or NaN
            continue
        fig.add_scatterpolar(r=scores, theta=axes, name=row["Ticker"], fill="toself",
                             line={"color": color, "width": 2}, fillcolor=_rgba(color, .06),
                             hovertemplate="%{theta}: %{r:.0f}<extra>" + row["Ticker"] + "</extra>")
    fig.update_layout(
        polar={"bgcolor": "rgba(0,0,0,0)",
               "radialaxis": {"range": [0, 100], "gridcolor": T.GRID,
                              "showticklabels": False, "linecolor": "rgba(0,0,0,0)"},
               "angularaxis": {"gridcolor": T.GRID, "linecolor": T.BORDER,
                               "tickfont": {"color": T.TEXT, "family": "Source Serif 4", "size": 12}}},
    )
    fig = _style(fig, height=460)
    fig.update_layout(hovermode="closest", legend={"y": -0.08, "orientation": "h"},
                      margin={"l": 70, "r": 70, "t": 40, "b": 40})  # room for the axis labels on phones
    return fig
