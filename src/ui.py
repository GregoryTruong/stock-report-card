"""Visual building blocks: the dark theme, report card widgets and chart styling."""

import html

import pandas as pd
import plotly.graph_objects as go

# Colors carry meaning: green = good grade, red = bad grade, blue = the stock,
# gray = the market. Each grade has a bright color for text and rings, and a
# see-through version of it for chip backgrounds.
GRADE_COLORS = {
    "A": "#34D399",
    "B": "#A3E635",
    "C": "#FBBF24",
    "D": "#FB923C",
    "F": "#F87171",
    "N/A": "#94A3B8",
}
# One short verdict per overall grade, shown under the big grade ring.
VERDICTS = {
    "A": "Top of the class",
    "B": "Strong all-rounder",
    "C": "Middle of the pack",
    "D": "Needs work",
    "F": "Struggling",
    "N/A": "Not enough data",
}
CATEGORY_ICONS = {"Growth": "🚀", "Profitability": "💰", "Valuation": "🏷️", "Risk": "🛡️"}

STOCK_COLOR = "#60A5FA"
MARKET_COLOR = "#64748B"
GAIN_COLOR = "#34D399"
LOSS_COLOR = "#F87171"
TEXT = "#E6EAF2"
MUTED = "#8B95A7"
CARD = "rgba(19, 26, 38, 0.72)"
BORDER = "rgba(148, 163, 184, 0.14)"
MONO = "'JetBrains Mono', 'IBM Plex Mono', monospace"
DISPLAY = "'Space Grotesk', 'IBM Plex Sans', sans-serif"


def _rgba(hex_color: str, alpha: float) -> str:
    """'#34D399', 0.15 -> 'rgba(52, 211, 153, 0.15)'."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def grade_color(grade: str) -> str:
    return GRADE_COLORS.get(grade, GRADE_COLORS["N/A"])


FONTS_URL = ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700"
             "&family=JetBrains+Mono:wght@400;600&display=swap")

CSS = f"""
<style>
@import url("{FONTS_URL}");
/* Soft blue glow behind the whole app, like city lights at night. */
.stApp {{
  background:
    radial-gradient(1200px 600px at 15% -10%, rgba(59, 130, 246, 0.18), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(14, 165, 233, 0.10), transparent 60%),
    #0B0F17;
}}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ font-family: {DISPLAY} !important; letter-spacing: -0.02em; }}

@keyframes rc-rise {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes rc-grow {{ from {{ width: 0; }} }}
@keyframes rc-ring {{ from {{ opacity: 0; transform: rotate(-120deg) scale(.85); }} }}
@keyframes rc-pulse {{ 0%, 100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}

.rc-rise {{ animation: rc-rise .6s cubic-bezier(.2, .7, .2, 1) both; }}

/* Hero */
.rc-hero {{ padding: 8px 0 20px; }}
.rc-eyebrow {{ display: inline-flex; align-items: center; gap: 8px; font-family: {MONO};
  font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: {STOCK_COLOR};
  padding: 5px 12px; border: 1px solid {_rgba(STOCK_COLOR, .35)}; border-radius: 999px;
  background: {_rgba(STOCK_COLOR, .08)}; }}
.rc-eyebrow .dot {{ width: 6px; height: 6px; border-radius: 50%; background: {STOCK_COLOR};
  box-shadow: 0 0 10px {STOCK_COLOR}; animation: rc-pulse 2s infinite; }}
.rc-hero h1 {{ font-size: clamp(2rem, 4.5vw, 3.2rem); line-height: 1.05; margin: 14px 0 8px;
  padding: 0; font-weight: 700; color: {TEXT}; }}
.rc-hero h1 span {{ background: linear-gradient(90deg, #60A5FA, #22D3EE 60%, #A5F3FC);
  -webkit-background-clip: text; background-clip: text; color: transparent; }}
.rc-hero p {{ color: {MUTED}; font-size: 1.02rem; max-width: 620px; margin: 0; }}

/* Cards */
.rc-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px;
  padding: 20px; backdrop-filter: blur(8px); }}

/* Company header */
.rc-header {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: 16px; margin: 8px 0 16px; }}
.rc-name {{ font-family: {DISPLAY}; font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 700;
  line-height: 1.1; color: {TEXT}; }}
.rc-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
.rc-tag {{ font-size: .78rem; color: {MUTED}; padding: 3px 10px; border-radius: 999px;
  border: 1px solid {BORDER}; background: rgba(255, 255, 255, .03); }}
.rc-tag.ticker {{ font-family: {MONO}; color: {STOCK_COLOR}; border-color: {_rgba(STOCK_COLOR, .4)}; }}
.rc-price {{ font-family: {MONO}; font-size: clamp(1.6rem, 3vw, 2.1rem); font-weight: 600;
  text-align: right; color: {TEXT}; }}
.rc-change {{ display: inline-block; font-family: {MONO}; font-size: .85rem; font-weight: 600;
  padding: 3px 10px; border-radius: 999px; float: right; margin-top: 4px; }}

/* Stat tiles */
.rc-stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 8px; }}
.rc-stat {{ padding: 16px 18px; }}
.rc-stat .k {{ font-size: .75rem; color: {MUTED}; text-transform: uppercase; letter-spacing: .08em; }}
.rc-stat .v {{ font-family: {MONO}; font-size: 1.45rem; font-weight: 600; color: {TEXT}; margin-top: 6px; }}
.rc-stat .d {{ font-family: {MONO}; font-size: .78rem; margin-top: 4px; }}

/* Report card: ring + category cards */
.rc-report {{ display: grid; grid-template-columns: 260px 1fr; gap: 16px; margin: 4px 0 8px; }}
.rc-overall {{ display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: 6px; }}
.rc-ring {{ position: relative; width: 150px; height: 150px; }}
.rc-ring .arc {{ position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), rgba(255, 255, 255, .07) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 11px), #000 calc(100% - 10px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 11px), #000 calc(100% - 10px));
  filter: drop-shadow(0 0 6px var(--c)); animation: rc-ring 1.2s cubic-bezier(.2, .7, .2, 1) both; }}
.rc-ring .letter {{ position: absolute; inset: 0; display: grid; place-items: center;
  font-family: {DISPLAY}; font-size: 3.6rem; font-weight: 700; }}
.rc-overall .verdict {{ font-family: {DISPLAY}; font-size: 1.15rem; font-weight: 600; color: {TEXT}; }}
.rc-overall .score {{ font-family: {MONO}; font-size: .85rem; color: {MUTED}; }}
.rc-cats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
.rc-cat {{ position: relative; overflow: hidden; transition: transform .2s, border-color .2s; }}
.rc-cat:hover {{ transform: translateY(-2px); border-color: rgba(148, 163, 184, .32); }}
.rc-cat::before {{ content: ""; position: absolute; inset: 0 auto 0 0; width: 3px; background: var(--c); }}
.rc-cat .top {{ display: flex; justify-content: space-between; align-items: center; }}
.rc-cat .name {{ font-family: {DISPLAY}; font-size: 1.05rem; font-weight: 600; color: {TEXT}; }}
.rc-cat .icon {{ margin-right: 8px; }}
.rc-cat .bar {{ height: 6px; border-radius: 3px; background: rgba(255, 255, 255, .07);
  margin: 14px 0 10px; overflow: hidden; }}
.rc-cat .bar span {{ display: block; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, {_rgba('#FFFFFF', .15)}, var(--c));
  box-shadow: 0 0 12px var(--c); animation: rc-grow 1s cubic-bezier(.2, .7, .2, 1) both; }}
.rc-cat .meta {{ display: flex; justify-content: space-between; font-size: .88rem; color: {MUTED}; gap: 12px; }}
.rc-cat .meta b {{ font-family: {MONO}; color: {TEXT}; font-weight: 600; white-space: nowrap; }}

.rc-chip {{ display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px;
  border-radius: 10px; font-family: {DISPLAY}; font-weight: 700; font-size: 1.1rem; }}

/* Compare podium */
.rc-podium {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px;
  align-items: end; margin: 8px 0 20px; }}
.rc-place {{ text-align: center; }}
.rc-place .medal {{ font-size: 1.8rem; }}
.rc-place .tk {{ font-family: {MONO}; font-size: 1.3rem; font-weight: 600; color: {TEXT}; margin-top: 4px; }}
.rc-place .co {{ font-size: .82rem; color: {MUTED}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.rc-place .sc {{ font-family: {MONO}; font-size: .85rem; color: {MUTED}; margin-top: 8px; }}
.rc-place.first {{ padding-top: 32px; padding-bottom: 32px; border-color: rgba(251, 191, 36, .45);
  box-shadow: 0 0 40px rgba(251, 191, 36, .08); }}

/* Plain tables (methodology) */
table.rc-table {{ width: 100%; border-collapse: collapse; }}
table.rc-table th {{ text-align: left; color: {MUTED}; font-weight: 500; font-size: .8rem;
  padding: 8px 12px; border-bottom: 1px solid {BORDER}; }}
table.rc-table td {{ padding: 10px 12px; border-bottom: 1px solid rgba(148, 163, 184, .07); color: {TEXT}; }}

/* Streamlit widgets, tuned to the theme */
[data-testid="stSidebar"] {{ background: rgba(11, 15, 23, .85); border-right: 1px solid {BORDER}; }}
[data-testid="stTabs"] button p {{ font-family: {DISPLAY}; font-weight: 600; }}
[data-testid="stExpander"] details {{ background: {CARD}; border-radius: 14px; border-color: {BORDER}; }}
[data-testid="stPlotlyChart"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px; padding: 8px; }}

@media (max-width: 900px) {{
  .rc-report {{ grid-template-columns: 1fr; }}
  .rc-stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 560px) {{
  .rc-cats, .rc-podium {{ grid-template-columns: 1fr; }}
  .rc-price, .rc-change {{ text-align: left; float: none; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before {{ animation: none !important; transition: none !important; }}
}}
</style>
"""


def grade_chip(grade: str) -> str:
    color = grade_color(grade)
    return (f'<span class="rc-chip" style="color:{color};background:{_rgba(color, .14)};'
            f'border:1px solid {_rgba(color, .35)}">{grade}</span>')


def hero_html() -> str:
    return """
    <div class="rc-hero rc-rise">
      <span class="rc-eyebrow"><span class="dot"></span>Stock Report Card</span>
      <h1>Grade any stock <span>in seconds.</span></h1>
      <p>Growth, profitability, valuation and risk, scored A to F and measured against
         the S&amp;P 500. Search a company or tap a pick below.</p>
    </div>"""


def format_price(value, currency="USD") -> str:
    """$12.34 for US dollars, otherwise 12.34 CAD (or whatever the currency is)."""
    return f"${value:,.2f}" if currency == "USD" else f"{value:,.2f} {currency}"


def header_html(name, ticker, subtitle, price, change, currency="USD") -> str:
    color = GAIN_COLOR if change >= 0 else LOSS_COLOR
    arrow = "▲" if change >= 0 else "▼"
    tags = "".join(f'<span class="rc-tag">{html.escape(t)}</span>' for t in subtitle.split(" · ") if t)
    return f"""
    <div class="rc-header rc-rise">
      <div>
        <div class="rc-name">{html.escape(name)}</div>
        <div class="rc-tags"><span class="rc-tag ticker">{html.escape(ticker)}</span>{tags}</div>
      </div>
      <div>
        <div class="rc-price">{format_price(price, currency)}</div>
        <span class="rc-change" style="color:{color};background:{_rgba(color, .12)}">
          {arrow} {abs(change):.2%} today</span>
      </div>
    </div>"""


def stats_html(stats) -> str:
    """A row of stat tiles. Each stat is (label, value, delta text or None, delta is good)."""
    tiles = ""
    for i, (label, value, delta, good) in enumerate(stats):
        delta_html = ""
        if delta:
            color = GAIN_COLOR if good else LOSS_COLOR
            delta_html = f'<div class="d" style="color:{color}">{html.escape(delta)}</div>'
        tiles += f"""
        <div class="rc-card rc-stat rc-rise" style="animation-delay:{i * 60}ms">
          <div class="k">{html.escape(label)}</div><div class="v">{html.escape(value)}</div>{delta_html}
        </div>"""
    return f'<div class="rc-stats">{tiles}</div>'


def _ring(grade: str, score) -> str:
    """A circular progress ring drawn with a CSS conic gradient (Streamlit strips inline SVG)."""
    color = grade_color(grade)
    return f"""
    <div class="rc-ring" style="--c:{color};--p:{score or 0:.1f}">
      <div class="arc"></div>
      <div class="letter" style="color:{color};text-shadow:0 0 24px {_rgba(color, .45)}">{grade}</div>
    </div>"""


def scorecard_html(card: dict) -> str:
    """The overall grade ring plus one card per category."""
    overall = card["overall_score"]
    grade = card["overall_grade"]
    overall_text = f"{overall:.0f} / 100" if overall is not None else "No data"
    cats = ""
    for i, (name, category) in enumerate(card["categories"].items()):
        score = category["score"]
        color = grade_color(category["grade"])
        width = 0 if score is None else score
        score_text = "-" if score is None else f"{score:.0f}/100"
        cats += f"""
        <div class="rc-card rc-cat rc-rise" style="--c:{color};animation-delay:{150 + i * 90}ms">
          <div class="top">
            <div class="name"><span class="icon">{CATEGORY_ICONS.get(name, "")}</span>{name}</div>
            {grade_chip(category["grade"])}
          </div>
          <div class="bar"><span style="width:{width}%;animation-delay:{300 + i * 90}ms"></span></div>
          <div class="meta"><span>{html.escape(category["summary"])}</span><b>{score_text}</b></div>
        </div>"""
    return f"""
    <div class="rc-report">
      <div class="rc-card rc-overall rc-rise">
        {_ring(grade, overall)}
        <div class="verdict">{VERDICTS.get(grade, "")}</div>
        <div class="score">Overall · {overall_text}</div>
      </div>
      <div class="rc-cats">{cats}</div>
    </div>"""


def podium_html(ranked: pd.DataFrame) -> str:
    """The top three stocks, with first place in the middle like a real podium."""
    top = ranked.head(3).to_dict("records")
    if not top:
        return ""
    medals = ["🥇", "🥈", "🥉"]
    places = [(row, medals[i], i) for i, row in enumerate(top)]
    order = [places[i] for i in (1, 0, 2) if i < len(places)] if len(places) >= 2 else places
    html_places = ""
    for row, medal, rank in order:
        html_places += f"""
        <div class="rc-card rc-place rc-rise{' first' if rank == 0 else ''}" style="animation-delay:{rank * 120}ms">
          <div class="medal">{medal}</div>
          <div class="tk">{html.escape(row["Ticker"])}</div>
          <div class="co">{html.escape(str(row["Company"]))}</div>
          <div style="margin-top:10px">{grade_chip(row["Overall"])}</div>
          <div class="sc">{row["Score"]:.0f} / 100</div>
        </div>"""
    return f'<div class="rc-podium">{html_places}</div>'


def grade_table_html() -> str:
    """The grade-to-score table on the Methodology page."""
    rows = "".join(
        f"<tr><td>{grade_chip(g)}</td><td>{s}</td><td>{VERDICTS[g]}</td></tr>"
        for g, s in (("A", "80 and up"), ("B", "65 to 79"), ("C", "50 to 64"),
                     ("D", "35 to 49"), ("F", "Under 35"))
    )
    return (f'<div class="rc-card"><table class="rc-table"><tr><th>Grade</th><th>Score</th>'
            f'<th>Verdict</th></tr>{rows}</table></div>')


def grade_cell_style(grade) -> str:
    """Used to color grade cells in the comparison table."""
    color = grade_color(grade)
    return f"color: {color}; background-color: {_rgba(color, .14)}; font-weight: 700"


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
        font={"family": "IBM Plex Sans, sans-serif", "size": 13, "color": TEXT},
        hovermode="x unified",
        hoverlabel={"bgcolor": "#131A26", "bordercolor": BORDER, "font": {"color": TEXT}},
        legend={"orientation": "h", "y": 1.1, "x": 0, "bgcolor": "rgba(0,0,0,0)"},
    )
    fig.update_xaxes(showgrid=False, linecolor=BORDER, tickfont={"color": MUTED})
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.08)", zeroline=False, tickfont={"color": MUTED})
    return fig


def _gradient(color: str, top_alpha: float) -> dict:
    """A fill that fades from the line color down to transparent."""
    return {"type": "vertical", "colorscale": [[0, _rgba(color, 0)], [1, _rgba(color, top_alpha)]]}


def growth_chart(stock: pd.Series, market: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=market.index, y=market, name="S&P 500 (SPY)",
                    line={"color": MARKET_COLOR, "width": 1.5, "dash": "dot"})
    fig.add_scatter(x=stock.index, y=stock, name=ticker, line={"color": STOCK_COLOR, "width": 2.5},
                    fill="tozeroy", fillgradient=_gradient(STOCK_COLOR, 0.35))
    # Mark where each line ends so the final values pop.
    for series, color in ((market, MARKET_COLOR), (stock, STOCK_COLOR)):
        fig.add_scatter(x=[series.index[-1]], y=[series.iloc[-1]], mode="markers", showlegend=False,
                        marker={"size": 9, "color": color, "line": {"width": 3, "color": _rgba(color, .3)}},
                        hoverinfo="skip")
    fig.add_hline(y=10_000, line={"color": "rgba(148, 163, 184, 0.25)", "width": 1, "dash": "dash"})
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", rangemode="tozero")
    fig.update_traces(hovertemplate="$%{y:,.0f}", selector={"mode": "lines"})
    return _style(fig)


def drawdown_chart(drawdown: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=drawdown.index, y=drawdown, name="Below peak", mode="lines",
                    line={"color": LOSS_COLOR, "width": 1.5}, fill="tozeroy",
                    fillgradient={"type": "vertical",
                                  "colorscale": [[0, _rgba(LOSS_COLOR, .4)], [1, _rgba(LOSS_COLOR, 0)]]},
                    hovertemplate="%{y:.1%}")
    worst = drawdown.idxmin()
    fig.add_annotation(x=worst, y=drawdown.min(), text=f"Worst: {drawdown.min():.0%}", showarrow=True,
                       arrowcolor=LOSS_COLOR, font={"color": LOSS_COLOR, "family": "JetBrains Mono"},
                       ay=30, bgcolor="#131A26", bordercolor=_rgba(LOSS_COLOR, .4))
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
        x=stocks["Volatility"], y=stocks["Yearly return"], mode="markers+text",
        text=stocks["Ticker"], textposition="top center", textfont={"family": "JetBrains Mono", "color": TEXT},
        marker={"size": 18, "color": [grade_color(g) for g in stocks["Overall"]],
                "line": {"width": 4, "color": [_rgba(grade_color(g), .25) for g in stocks["Overall"]]}},
        customdata=stocks["Overall"],
        hovertemplate="%{text} · grade %{customdata}<br>Return %{y:.1%}<br>Volatility %{x:.1%}<extra></extra>",
    )
    fig.add_scatter(
        x=market["Volatility"], y=market["Yearly return"], mode="markers+text", text=["S&P 500"],
        textposition="bottom center", textfont={"color": MUTED},
        marker={"size": 14, "color": MARKET_COLOR, "symbol": "diamond"},
        hovertemplate="S&P 500<br>Return %{y:.1%}<br>Volatility %{x:.1%}<extra></extra>",
    )
    if len(market):
        fig.add_vline(x=market["Volatility"].iloc[0], line={"color": "rgba(148,163,184,.2)", "dash": "dot"})
        fig.add_hline(y=market["Yearly return"].iloc[0], line={"color": "rgba(148,163,184,.2)", "dash": "dot"})
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
    palette = ["#60A5FA", "#F472B6", "#34D399", "#FBBF24", "#A78BFA", "#22D3EE", "#FB923C", "#F87171"]
    axes = [*categories, categories[0]]  # repeat the first point to close the shape
    fig = go.Figure()
    for i, row in enumerate(table.to_dict("records")):
        color = palette[i % len(palette)]
        scores = [row.get(f"{c} score") for c in axes]
        if any(score is None or score != score for score in scores):  # None or NaN
            continue
        fig.add_scatterpolar(r=scores, theta=axes, name=row["Ticker"], fill="toself",
                             line={"color": color, "width": 2}, fillcolor=_rgba(color, .12),
                             hovertemplate="%{theta}: %{r:.0f}<extra>" + row["Ticker"] + "</extra>")
    fig.update_layout(
        polar={"bgcolor": "rgba(0,0,0,0)",
               "radialaxis": {"range": [0, 100], "gridcolor": "rgba(148,163,184,.12)",
                              "showticklabels": False, "linecolor": "rgba(0,0,0,0)"},
               "angularaxis": {"gridcolor": "rgba(148,163,184,.12)", "linecolor": BORDER,
                               "tickfont": {"color": TEXT, "family": "Space Grotesk", "size": 14}}},
    )
    fig = _style(fig, height=460)
    fig.update_layout(hovermode="closest", legend={"y": -0.08, "orientation": "h"})
    return fig
