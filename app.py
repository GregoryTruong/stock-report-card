"""Stock Report Card: the web app. Run it with:  streamlit run app.py"""

import pandas as pd
import streamlit as st

from src import ui
from src.data import MARKET_TICKER, get_company_info, get_price_history, rank_matches, search_tickers
from src.grading import CATEGORIES, build_report_card
from src.metrics import collect_metrics, drawdown_series, growth_of_10k

st.set_page_config(page_title="Stock Report Card", page_icon="📈", layout="wide")
st.html(ui.CSS)

# Ready-made groups of tickers so people can explore without knowing symbols.
PRESETS = {
    "Car makers": ["TSLA", "F", "GM", "TM", "RIVN", "HMC"],
    "Gaming": ["NVDA", "AMD", "SONY", "NTDOY", "TTWO", "RBLX"],
    "Big tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "Everyday brands": ["KO", "PEP", "PG", "WMT", "MCD", "NKE"],
}
PERIODS = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "10Y": "10y"}


# st.cache_data saves results for an hour so we don't re-download
# the same data every time the page refreshes.
@st.cache_data(ttl=3600, show_spinner=False)
def load_stock(ticker: str, period: str):
    prices = get_price_history(ticker, period)
    market_prices = get_price_history(MARKET_TICKER, period)
    info = get_company_info(ticker)
    metrics = collect_metrics(info, prices, market_prices)
    return info, prices, market_prices, metrics, build_report_card(metrics)


@st.cache_data(ttl=86400, show_spinner=False)
def search_cached(query: str):
    return search_tickers(query)


def find_stocks(query: str):
    """Search by company name or ticker, with an exact ticker match first.

    If Yahoo's search is down or errors, we still try the query as a ticker.
    """
    try:
        matches = search_cached(query)
    except Exception:
        matches = []
    return rank_matches(query, matches)


def use_preset_ticker():
    """When a quick-pick ticker is clicked, put it in the search box."""
    if st.session_state.quick_pick:
        st.session_state.query = st.session_state.quick_pick


def use_preset_group():
    """When a group is clicked on the Compare page, fill in its tickers."""
    if st.session_state.compare_group:
        st.session_state.compare_input = ", ".join(PRESETS[st.session_state.compare_group])


# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.markdown("### 📈 Stock Report Card")
    page_icons = {"Report card": "🎓", "Compare": "⚔️", "Methodology": "📐"}
    page = st.radio("Page", list(page_icons), format_func=lambda p: f"{page_icons[p]}  {p}",
                    label_visibility="collapsed")
    st.divider()
    period_label = st.segmented_control("Time period", list(PERIODS), default="5Y",
                                        help="Used for the risk metrics and the charts.")
    period = PERIODS.get(period_label or "5Y")
    st.caption("For learning purposes only. Not financial advice.")


# -------------------------------------------------------------- Report card
def report_card_page():
    if "query" not in st.session_state:
        st.session_state.query = "AAPL"

    st.html(ui.hero_html())
    search, picks = st.columns([1, 2], vertical_alignment="bottom")
    with search:
        st.text_input("Search a company or ticker", key="query",
                      placeholder="e.g. Aritzia or AAPL")
    with picks:
        group = st.selectbox("Browse", list(PRESETS), label_visibility="collapsed")
    st.pills("Quick picks", PRESETS[group], key="quick_pick", on_change=use_preset_ticker,
             label_visibility="collapsed")

    query = st.session_state.query.strip()
    if not query:
        return
    matches = find_stocks(query)
    if not matches:
        st.warning(f'No stocks found for "{query}". Try the full company name or a ticker.')
        return
    if len(matches) > 1:
        pick = st.selectbox(
            "Matches", range(len(matches)),
            format_func=lambda i: " · ".join(
                x for x in (matches[i]["symbol"], matches[i]["name"], matches[i]["exchange"]) if x),
        )
    else:
        pick = 0
    ticker = matches[pick]["symbol"]

    try:
        with st.spinner(f"Loading {ticker}..."):
            info, prices, market_prices, metrics, card = load_stock(ticker, period)
    except Exception as error:
        st.error(f"Couldn't load {ticker}: {error}")
        return

    day_change = prices.iloc[-1] / prices.iloc[-2] - 1
    subtitle = " · ".join(x for x in (info.get("sector"), info.get("industry")) if x) or "Fund"
    currency = info.get("currency") or "USD"
    st.html(ui.header_html(info.get("longName") or ticker, ticker, subtitle,
                           prices.iloc[-1], day_change, currency))

    excess = metrics["annual_return"] - metrics["market_annual_return"]
    cap_label = "Market cap" if currency == "USD" else f"Market cap ({currency})"
    st.html(ui.stats_html([
        (cap_label, ui.format_large_number(info.get("marketCap"), currency), None, True),
        (f"Yearly return · {period_label}", f"{metrics['annual_return']:.1%}",
         f"{excess:+.1%} vs S&P 500", excess >= 0),
        ("Worst drop", f"{metrics['max_drawdown']:.0%}", None, True),
        ("Beta", f"{metrics['beta']:.2f}",
         "calmer than market" if metrics["beta"] < 1 else "swings more than market", metrics["beta"] < 1),
    ]))

    st.html(ui.scorecard_html(card))

    with st.expander("See every metric behind the grades"):
        rows = [
            {"Category": name, **detail}
            for name, category in card["categories"].items()
            for detail in category["details"]
        ]
        st.dataframe(
            pd.DataFrame(rows), hide_index=True, use_container_width=True,
            column_config={"Score": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%.0f")},
        )

    st.subheader("Performance")
    growth_tab, drawdown_tab = st.tabs(["📈 Growth of $10,000", "📉 Drops from peak"])
    with growth_tab:
        st.plotly_chart(
            ui.growth_chart(growth_of_10k(prices), growth_of_10k(market_prices), ticker),
            use_container_width=True,
        )
    with drawdown_tab:
        st.caption("How far below its highest price the stock was on each day. "
                   "0% means it was at a high.")
        st.plotly_chart(ui.drawdown_chart(drawdown_series(prices)), use_container_width=True)


# ------------------------------------------------------------------ Compare
def compare_page():
    if "compare_input" not in st.session_state:
        st.session_state.compare_input = ", ".join(PRESETS["Car makers"])

    st.header("Compare stocks")
    st.text_input("Tickers, separated by commas", key="compare_input",
                  help="Non-US stocks need their exchange suffix, like ATZ.TO for Aritzia. "
                       "Search by name on the Report card page to find it.")
    st.pills("Load a group", list(PRESETS), key="compare_group", on_change=use_preset_group)

    tickers = [t.strip().upper() for t in st.session_state.compare_input.split(",") if t.strip()]
    rows = []
    with st.spinner("Loading..."):
        for t in dict.fromkeys(tickers + [MARKET_TICKER]):  # dedupe, keep order, add the market
            try:
                info, _, _, metrics, card = load_stock(t, period)
            except Exception as error:
                st.warning(f"Skipped {t}: {error}")
                continue
            row = {"Ticker": t, "Company": info.get("shortName") or t,
                   "Overall": card["overall_grade"], "Score": card["overall_score"] or 0}
            row.update({name: c["grade"] for name, c in card["categories"].items()})
            row.update({f"{name} score": c["score"] for name, c in card["categories"].items()})
            row["Yearly return"] = metrics["annual_return"]
            row["Volatility"] = metrics["volatility"]
            rows.append(row)

    if not rows:
        return
    table = pd.DataFrame(rows)
    ranked = table[table["Ticker"] != MARKET_TICKER].sort_values("Score", ascending=False)

    grade_columns = ["Overall", *CATEGORIES]
    st.html(ui.podium_html(ranked))
    score_columns = [f"{name} score" for name in CATEGORIES]
    st.dataframe(
        ranked.drop(columns=score_columns).style.map(ui.grade_cell_style, subset=grade_columns),
        hide_index=True, use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
            "Yearly return": st.column_config.NumberColumn(format="percent"),
            "Volatility": st.column_config.NumberColumn(format="percent"),
        },
    )

    st.subheader("Risk vs. return")
    st.caption("Each dot is a stock. Higher is better return, further right is a bumpier ride. "
               "The gray dot is the S&P 500, so anything above and left of it beat the "
               "market with less risk.")
    st.plotly_chart(ui.risk_return_chart(table), use_container_width=True)

    st.subheader("Strengths at a glance")
    st.caption("Each shape shows a stock's four category scores. The bigger the shape, the better "
               "the all-round grade. Click names in the legend to hide or show them.")
    st.plotly_chart(ui.radar_chart(ranked, list(CATEGORIES)), use_container_width=True)


# -------------------------------------------------------------- Methodology
def methodology_page():
    st.header("How the grading works")
    st.markdown(
        """
Each metric gets a **score from 0 to 100** based on where it falls between a
"worst" and a "best" cutoff. Each category is the average of its metrics, and
the overall grade is the average of the four categories.
"""
    )
    st.html(ui.grade_table_html())
    rows = [
        {"Category": name, "Metric": label,
         "Worst (score 0)": worst, "Best (score 100)": best,
         "Unit": "percent" if kind == "pct" else "ratio"}
        for name, rules in CATEGORIES.items()
        for label, _, worst, best, kind in rules
    ]
    st.subheader("Cutoffs")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown(
        """
**Growth:** is the company selling more and earning more than last year?

**Profitability:** how much of each sales dollar becomes profit (margin), and how
well it uses shareholders' money (return on equity).

**Valuation:** how much you pay for each dollar of profit or sales (P/E, P/S). Lower is cheaper.

**Risk:** volatility (daily swings), worst drop from a peak, and beta (how much the
stock moves when the S&P 500 moves).

**Limitations:** the cutoffs are general rules of thumb. Different industries have
different "normal" numbers (software has higher margins than grocery stores),
and a good grade doesn't mean the price will go up.
"""
    )


{"Report card": report_card_page, "Compare": compare_page, "Methodology": methodology_page}[page]()
