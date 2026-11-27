"""Stock Report Card: the web app. Run it with:  streamlit run app.py"""

import json
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src import ui
from src.data import MARKET_TICKER, get_company_info, get_price_history, rank_matches, search_tickers
from src.grading import CATEGORIES, build_report_card
from src.metrics import collect_metrics, drawdown_series, growth_of_10k

st.set_page_config(page_title="Stock Report Card", page_icon="assets/favicon.png", layout="wide")


def current_theme() -> str:
    """"dark" or "light". A ?theme= in the URL wins, because Streamlit's own reading of
    the theme can be wrong on the first load right after the switch reloads the page."""
    from_url = st.query_params.get("theme")
    if from_url in ("dark", "light"):
        return from_url
    theme_type = getattr(getattr(st.context, "theme", None), "type", None)
    return theme_type if theme_type in ("dark", "light") else "dark"


def plain(text) -> str:
    """Escape Markdown so text from the URL or Yahoo shows as-is (no sneaky links or formatting).

    Every ASCII punctuation mark gets a backslash, which also breaks up bare web
    addresses like www.example.com so they don't turn into live links.
    """
    return re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", str(text))


def switch_theme(mode: str):
    """Make Streamlit's theme match `mode` by saving it where Streamlit looks, then reloading.

    Streamlit has no Python call to change the theme, but it remembers each
    visitor's pick in the browser's localStorage. The page, ticker and time
    period are kept in the URL, so the reload lands right back where you were.
    It only reloads when the saved theme is different, so it never loops, and it
    also runs when a shared link carries ?theme=, so the colors always match.
    """
    choice = json.dumps("Dark" if mode == "dark" else "Light")
    components.html(f"""<script>
      const w = window.parent;
      const key = `stActiveTheme-${{w.location.pathname}}-v2`;
      const url = new URL(w.location.href);
      url.searchParams.set("theme", {json.dumps(mode)});
      w.history.replaceState(null, "", url.toString());
      try {{
        if (w.localStorage.getItem(key) !== JSON.stringify({choice})) {{
          w.localStorage.setItem(key, JSON.stringify({choice}));
          w.location.reload();  // a plain reload is allowed from here, navigating isn't
        }}
      }} catch (e) {{}}  // storage blocked (private window): keep the page as it is
    </script>""", height=0)


THEME = current_theme()
ui.set_theme(THEME)
st.html(ui.css())

# Stocks and funds I follow, with a short note on what each one is.
WATCHLIST = {
    "NVDA": "Nvidia. Graphics cards for gaming, and the chips behind most AI data centers.",
    "MU": "Micron. Memory chips: the RAM and storage in phones, PCs and AI servers.",
    "VST": "Vistra. A US power company running gas, nuclear and solar plants.",
    "OKLO": "Oklo. A nuclear startup designing small reactors. No sales yet, so expect low grades.",
    "VFV.TO": "Vanguard S&P 500 index fund, in Canadian dollars. Funds don't get an overall grade.",
    "QQC.TO": "A Nasdaq 100 index fund, in Canadian dollars. Funds don't get an overall grade.",
    "XEQT.TO": "iShares all-equity fund: thousands of stocks worldwide in one. Funds don't get an overall grade.",
}

# Ready-made groups of tickers so people can explore without knowing symbols.
PRESETS = {
    "My watchlist": list(WATCHLIST),
    "Car makers": ["TSLA", "F", "GM", "TM", "RIVN", "HMC"],
    "Gaming": ["NVDA", "AMD", "SONY", "NTDOY", "TTWO", "RBLX"],
    "Big tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "Everyday brands": ["KO", "PEP", "PG", "WMT", "MCD", "NKE"],
}
WHY_I_BUILT_THIS = """
I wanted to open a TFSA and stop leaving my money in a savings account where it barely
grew. Before putting money into a stock, I wanted a quick way to tell whether the company
behind it was actually any good. So I picked four things analysts look at, set a cutoff
for each, and made the app explain every grade in plain English.

The watchlist is the mix of stocks and index funds I actually follow.
"""
PERIODS = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "10Y": "10y"}
PAGES = ["Report card", "Compare", "Methodology", "Terms & privacy"]

# The page, search and time period live in the URL (e.g. ?page=Compare&q=TSLA),
# so links can be shared and switching themes doesn't lose your place.
params = st.query_params
if "query" not in st.session_state:
    st.session_state.query = params.get("q", "NVDA")
if "page" not in st.session_state:
    st.session_state.page = params.get("page") if params.get("page") in PAGES else "Report card"
if "period_label" not in st.session_state:
    st.session_state.period_label = params.get("period") if params.get("period") in PERIODS else "5Y"


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
    st.markdown("### Stock Report Card")
    page = st.radio("Page", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    period_label = st.segmented_control("Time period", list(PERIODS), key="period_label",
                                        help="Used for the risk metrics and the charts.")
    period = PERIODS.get(period_label or "5Y")
    st.divider()
    dark_mode = st.toggle("Dark mode", value=THEME == "dark")
    if dark_mode != (THEME == "dark"):
        switch_theme("dark" if dark_mode else "light")
    elif st.query_params.get("theme") in ("dark", "light"):
        switch_theme(THEME)  # a shared link with ?theme= : bring Streamlit's own theme in line
    st.caption("For learning purposes only. Not financial advice.")

st.query_params.update(page=page, period=period_label or "5Y", q=st.session_state.query)


# -------------------------------------------------------------- Report card
def report_card_page():
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
        st.warning(f'No stocks found for "{plain(query)}". Try the full company name or a ticker.')
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

    placeholder = st.empty()
    placeholder.html(ui.skeleton_html())  # the shape of the page, until the data arrives
    try:
        info, prices, market_prices, metrics, card = load_stock(ticker, period)
    except Exception as error:
        placeholder.empty()
        st.error(f"Couldn't load {plain(ticker)}: {plain(error)}")
        return
    placeholder.empty()

    day_change = prices.iloc[-1] / prices.iloc[-2] - 1
    subtitle = " · ".join(x for x in (info.get("sector"), info.get("industry")) if x) or "Fund"
    currency = info.get("currency") or "USD"
    st.html(ui.header_html(info.get("longName") or ticker, ticker, subtitle,
                           prices.iloc[-1], day_change, currency))

    if ticker in WATCHLIST:
        st.caption(f"On my watchlist: {WATCHLIST[ticker]}")

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
            pd.DataFrame(rows), hide_index=True, width="stretch",
            column_config={"Score": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%.0f")},
        )

    st.subheader("Performance")
    growth_tab, drawdown_tab = st.tabs(["Growth of $10,000", "Drops from peak"])
    with growth_tab:
        st.plotly_chart(
            ui.growth_chart(growth_of_10k(prices), growth_of_10k(market_prices), ticker),
            width="stretch",
        )
    with drawdown_tab:
        st.caption("How far below its highest price the stock was on each day. "
                   "0% means it was at a high.")
        st.plotly_chart(ui.drawdown_chart(drawdown_series(prices)), width="stretch")


# ------------------------------------------------------------------ Compare
def compare_page():
    if "compare_input" not in st.session_state:
        st.session_state.compare_input = ", ".join(PRESETS["My watchlist"])

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
                st.warning(f"Skipped {plain(t)}: {plain(error)}")
                continue
            row = {"Ticker": t, "Company": info.get("shortName") or t,
                   "Overall": card["overall_grade"], "Score": card["overall_score"]}
            row.update({name: c["grade"] for name, c in card["categories"].items()})
            row.update({f"{name} score": c["score"] for name, c in card["categories"].items()})
            row["Yearly return"] = metrics["annual_return"]
            row["Volatility"] = metrics["volatility"]
            rows.append(row)

    if not rows:
        return
    table = pd.DataFrame(rows)
    ranked = table[table["Ticker"] != MARKET_TICKER].sort_values("Score", ascending=False, na_position="last")

    grade_columns = ["Overall", *CATEGORIES]
    st.html(ui.top_three_html(ranked))
    score_columns = [f"{name} score" for name in CATEGORIES]
    st.dataframe(
        ranked.drop(columns=score_columns).style.map(ui.grade_cell_style, subset=grade_columns),
        hide_index=True, width="stretch",
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
    st.plotly_chart(ui.risk_return_chart(table), width="stretch")

    st.subheader("Strengths at a glance")
    st.caption("Each shape shows a stock's four category scores. The bigger the shape, the better "
               "the all-round grade. Click names in the legend to hide or show them.")
    st.plotly_chart(ui.radar_chart(ranked, list(CATEGORIES)), width="stretch")


# -------------------------------------------------------------- Methodology
def methodology_page():
    st.header("Why I built this")
    st.markdown(WHY_I_BUILT_THIS)
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
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(
        """
**Growth:** is the company selling more and earning more than last year?

**Profitability:** how much of each sales dollar becomes profit (margin), and how
well it uses shareholders' money (return on equity).

**Valuation:** how much you pay for each dollar of profit or sales (P/E, P/S). Lower is cheaper.

**Risk:** volatility (daily swings), worst drop from a peak, and beta (how much the
stock moves when the S&P 500 moves).

**Why these cutoffs.** Each one is my own call, based on what's normal for a big
US company:

- **Profit margin, best at 25%.** S&P 500 companies have kept about 11 to 13 cents of each
  sales dollar as profit in recent years (less over the long run), so 25% is about double that. Zero or less scores 0.
- **Revenue growth, best at 25% a year.** Most large companies grow in the single digits,
  so 25% is fast. Shrinking scores 0.
- **P/E, best at 12 and worst at 40.** The S&P 500 has averaged around 16 over the long
  run. Under 12 is cheap; over 40 means investors are paying for a lot of growth that
  hasn't happened yet. A company losing money gets the worst score.
- **Volatility, best at 15% a year.** That's close to how much the S&P 500 itself swings
  in a typical year. At 60%, the price can halve or double within a year.
- **Funds get no overall grade.** An index fund like SPY has no sales or profit of its own,
  so it would be graded on risk alone and beat every real company. I found that bug while
  testing the Compare page, so now a stock needs Growth or Profitability data to get an
  overall grade.

**Limitations:** the cutoffs are general rules of thumb. Different industries have
different "normal" numbers (software has higher margins than grocery stores),
and a good grade doesn't mean the price will go up.
"""
    )


# ---------------------------------------------------------- Terms & privacy
def terms_page():
    st.header("Terms and privacy")
    st.caption("Last updated November 27, 2026")
    st.markdown(
        """
**What this is.** Stock Report Card is a student project that turns public market data
into letter grades. It's for learning. Nothing here is financial advice, a recommendation
to buy or sell anything, or a promise about how a stock will do.

**Where the numbers come from.** Prices and company data come from Yahoo Finance through
the open-source yfinance library. That data can be late, missing or wrong, and the grades
are only as good as the data behind them. Yahoo's data is meant for personal use, so please
don't scrape this site or resell what it shows.

**What the app collects.** Nothing that identifies you. There are no accounts, no sign-ups
and no ads, and the app doesn't add any tracking or analytics of its own (Streamlit's usage
stats are switched off). What you type in the search box is sent to Yahoo Finance to
look up the stock, and it shows up in the page address so links can be shared. Your
dark or light mode choice is saved in your own browser.

**Hosting.** The app runs on Streamlit Community Cloud. Streamlit keeps its own server logs,
and if you're signed in to Streamlit it may show the app owner that you viewed the app. That
part is covered by Streamlit's privacy policy, not this page.

**Questions or problems.** Open an issue on the
[GitHub repository](https://github.com/GregoryTruong/stock-report-card/issues).
"""
    )


{"Report card": report_card_page, "Compare": compare_page, "Methodology": methodology_page,
 "Terms & privacy": terms_page}[page]()
