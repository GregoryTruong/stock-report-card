"""Visual building blocks: grade colors, the scorecard table and chart styling."""

import html

import pandas as pd
import plotly.graph_objects as go

# Colors carry meaning: green = good grade, red = bad grade, teal = the stock,
# gray = the market. (text color, background color) for each grade.
GRADE_COLORS = {
    "A": ("#166534", "#DCFCE7"),
    "B": ("#3F6212", "#ECFCCB"),
    "C": ("#92400E", "#FEF3C7"),
    "D": ("#9A3412", "#FFEDD5"),
    "F": ("#991B1B", "#FEE2E2"),
    "N/A": ("#4B5563", "#F3F4F6"),
}
STOCK_COLOR = "#0F766E"
MARKET_COLOR = "#9CA3AF"
GAIN_COLOR = "#15803D"
LOSS_COLOR = "#B91C1C"
MUTED = "#5B6170"
MONO = "'IBM Plex Mono', monospace"

CSS = f"""
<style>
.rc-header {{ display: flex; justify-content: space-between; align-items: flex-end;
  flex-wrap: wrap; gap: 16px; padding-bottom: 16px; margin-bottom: 8px;
  border-bottom: 1px solid #DFE2E6; }}
.rc-name {{ font-size: 1.75rem; font-weight: 600; line-height: 1.2; }}
.rc-sub {{ color: {MUTED}; font-size: 0.9rem; margin-top: 4px; }}
.rc-price {{ font-family: {MONO}; font-size: 1.75rem; font-weight: 500; text-align: right; }}
.rc-change {{ font-family: {MONO}; font-size: 0.9rem; text-align: right; }}
.rc-chip {{ display: inline-flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 6px; font-family: {MONO}; font-weight: 500; }}
.rc-chip.lg {{ width: 64px; height: 64px; font-size: 2rem; border-radius: 8px; }}
.rc-overall {{ display: flex; align-items: center; gap: 16px; margin: 8px 0 16px; }}
.rc-overall .label {{ color: {MUTED}; font-size: 0.85rem; }}
.rc-overall .score {{ font-family: {MONO}; font-size: 1.1rem; }}
table.rc-card {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; }}
table.rc-card th {{ text-align: left; color: {MUTED}; font-weight: 500; font-size: 0.8rem;
  padding: 8px 12px; border-bottom: 1px solid #DFE2E6; }}
table.rc-card td {{ padding: 12px; border-bottom: 1px solid #EEF0F2; vertical-align: middle; }}
.rc-bar {{ display: inline-block; width: 120px; height: 6px; background: #EEF0F2;
  border-radius: 3px; overflow: hidden; vertical-align: middle; }}
.rc-bar span {{ display: block; height: 100%; }}
.rc-num {{ font-family: {MONO}; font-size: 0.85rem; color: {MUTED}; margin-left: 8px; }}
.rc-nowrap {{ white-space: nowrap; }}
</style>
"""


def grade_chip(grade: str, large: bool = False) -> str:
    text, background = GRADE_COLORS.get(grade, GRADE_COLORS["N/A"])
    size = " lg" if large else ""
    return f'<span class="rc-chip{size}" style="color:{text};background:{background}">{grade}</span>'


def header_html(name, ticker, subtitle, price, change) -> str:
    color = GAIN_COLOR if change >= 0 else LOSS_COLOR
    sign = "+" if change >= 0 else ""
    return f"""
    <div class="rc-header">
      <div>
        <div class="rc-name">{html.escape(name)}</div>
        <div class="rc-sub">{html.escape(ticker)} · {html.escape(subtitle)}</div>
      </div>
      <div>
        <div class="rc-price">${price:,.2f}</div>
        <div class="rc-change" style="color:{color}">{sign}{change:.2%} today</div>
      </div>
    </div>"""


def scorecard_html(card: dict) -> str:
    """The overall grade plus one table row per category."""
    overall = card["overall_score"]
    overall_text = f"{overall:.0f} / 100" if overall is not None else "No data"
    rows = ""
    for name, category in card["categories"].items():
        score = category["score"]
        text_color, _ = GRADE_COLORS.get(category["grade"], GRADE_COLORS["N/A"])
        width = 0 if score is None else score
        score_text = "-" if score is None else f"{score:.0f}"
        rows += f"""
        <tr>
          <td style="font-weight:500">{name}</td>
          <td>{grade_chip(category["grade"])}</td>
          <td class="rc-nowrap"><span class="rc-bar"><span style="width:{width}%;background:{text_color}"></span></span>
              <span class="rc-num">{score_text}</span></td>
          <td style="color:{MUTED}">{html.escape(category["summary"])}</td>
        </tr>"""
    return f"""
    <div class="rc-overall">
      {grade_chip(card["overall_grade"], large=True)}
      <div><div class="label">Overall grade</div><div class="score">{overall_text}</div></div>
    </div>
    <table class="rc-card">
      <tr><th>Category</th><th>Grade</th><th>Score</th><th>What it means</th></tr>
      {rows}
    </table>"""


def grade_cell_style(grade) -> str:
    """Used to color grade cells in the comparison table."""
    text, background = GRADE_COLORS.get(grade, GRADE_COLORS["N/A"])
    return f"color: {text}; background-color: {background}; font-weight: 600"


def format_large_number(value) -> str:
    if not value:
        return "-"
    for limit, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(value) >= limit:
            return f"${value / limit:.2f}{suffix}"
    return f"${value:,.0f}"


def _style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="IBM Plex Sans, sans-serif", size=13, color="#16181D"),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#DFE2E6")
    fig.update_yaxes(gridcolor="#EEF0F2", zeroline=False)
    return fig


def growth_chart(stock: pd.Series, market: pd.Series, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=market.index, y=market, name="S&P 500 (SPY)",
                    line=dict(color=MARKET_COLOR, width=1.5))
    fig.add_scatter(x=stock.index, y=stock, name=ticker, line=dict(color=STOCK_COLOR, width=2))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_traces(hovertemplate="$%{y:,.0f}")
    return _style(fig)


def drawdown_chart(drawdown: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=drawdown.index, y=drawdown, fill="tozeroy", name="Below peak",
                    line=dict(color=LOSS_COLOR, width=1), fillcolor="rgba(185, 28, 28, 0.12)",
                    hovertemplate="%{y:.1%}")
    fig.update_yaxes(tickformat=".0%")
    return _style(fig, height=280)


def risk_return_chart(table: pd.DataFrame) -> go.Figure:
    """Classic finance chart: yearly return (up) vs. volatility (right).

    Up and to the left is the best place to be: high return, low risk.
    """
    is_market = table["Ticker"] == "SPY"
    fig = go.Figure()
    for subset, color, name in ((table[~is_market], STOCK_COLOR, "Stocks"),
                                (table[is_market], MARKET_COLOR, "S&P 500")):
        fig.add_scatter(
            x=subset["Volatility"], y=subset["Yearly return"], mode="markers+text",
            text=subset["Ticker"], textposition="top center", name=name,
            marker=dict(size=12, color=color),
            hovertemplate="%{text}<br>Return %{y:.1%}<br>Volatility %{x:.1%}<extra></extra>",
        )
    fig.update_xaxes(title="Volatility (yearly)", tickformat=".0%")
    fig.update_yaxes(title="Average yearly return", tickformat=".0%")
    fig = _style(fig, height=420)
    fig.update_layout(hovermode="closest", showlegend=False)
    return fig
