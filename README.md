# Stock Report Card

[![Tests](https://github.com/GregoryTruong/stock-report-card/actions/workflows/tests.yml/badge.svg)](https://github.com/GregoryTruong/stock-report-card/actions/workflows/tests.yml)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stock-report-card.streamlit.app)

**Live demo: [stock-report-card.streamlit.app](https://stock-report-card.streamlit.app)**

Type in a company, get a report card. The app pulls the stock from Yahoo Finance (US or
not: Aritzia on the Toronto exchange works too) and grades it **A to F** in four subjects:
**growth, profitability, valuation and risk**. Each grade comes with a one-line comment,
and the risk numbers are measured against the S&P 500.

I built it to practice the kind of breakdown an equity analyst writes up: pick a few
numbers that matter, set clear cutoffs, and explain the result in plain English. It doesn't
try to predict prices.

## Why I built this

I wanted to open a TFSA and stop leaving my money in a savings account where it barely
grew. Before putting money into a stock, I wanted a quick way to tell whether the company
behind it was actually any good. So I picked four things analysts look at, set a cutoff for
each, and made the app explain every grade in plain English. The app opens on my watchlist,
which is made of companies from things I'm into: tech, cars, sports, fashion and gaming.

## What's in it

- **Report card:** an overall grade, a grade and comment for each subject, and every
  metric behind them if you want to check the math.
- **Growth of $10,000:** what $10k in the stock would be worth today next to the same
  amount in the S&P 500.
- **Drops from peak:** how far the stock fell below its high, day by day.
- **Compare:** rank a list of tickers, with a risk vs. return chart.
- **My watchlist:** Aritzia, Shopify, Nvidia, Sony, Ferrari and Nike, each with a note on
  why it's there. The Methodology page explains why I picked each cutoff.
- **Dark and light mode**, and links that keep your stock, page and time period.

## How the grading works

| Category | Metrics | What it tells you |
|---|---|---|
| Growth | Revenue growth, earnings growth | Is the business getting bigger? |
| Profitability | Profit margin, return on equity | Does it actually make money? |
| Valuation | P/E (trailing + forward), price-to-sales | Is the stock cheap or expensive for what it earns? |
| Risk | Volatility, max drawdown, beta | How bumpy is the ride? |

Each metric is scaled to a **0-100 score** between a "worst" and "best" cutoff.
Categories average their metrics, and the overall grade averages the categories.
Risk metrics are calculated from 5 years of daily prices; the other metrics come
from Yahoo Finance company data.

## Tech stack

- **Python** with **pandas** and **NumPy** for the calculations
- **yfinance** to pull market data from Yahoo Finance
- **Streamlit** for the web app, **Plotly** for interactive charts
- **pytest** for unit tests that check the financial math

## Project structure

```
app.py               Web app: layout, charts, tabs
src/data.py          Downloads prices and company info
src/metrics.py       Financial math (returns, volatility, drawdown, beta)
src/grading.py       Converts metrics into scores and letter grades
src/ui.py            Both themes, the report card layout and chart styling
.streamlit/          App theme (colors and fonts)
tests/               Unit tests on made-up data with known answers
```

## Run it yourself

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
```

Run the tests with `pytest` and the linter with `ruff check .`.
Both run automatically on every push and pull request via GitHub Actions.

## Deploy it for free

The app runs on [Streamlit Community Cloud](https://streamlit.io/cloud) with no changes:

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. Click **Create app**, pick this repository, branch `main`, and main file `app.py`.
3. Under **Advanced settings**, choose Python 3.13, then click **Deploy**.

Streamlit installs `requirements.txt` and reads the theme from `.streamlit/config.toml`.
Every push to `main` redeploys the site automatically. Yahoo Finance sometimes rate-limits
shared cloud servers; the app caches data for an hour to keep requests low, and shows a
clear error if a download fails.

## Limitations and next steps

- The cutoffs are general rules of thumb. A software company and a grocery chain have
  very different "normal" margins, so a next step is grading against **industry peers**.
- Yahoo Finance data can be missing for some tickers (ETFs have no profit margin, for example).
- Good grades don't mean the price will go up. Nothing here is financial advice; see the
  Terms & privacy page in the app.
