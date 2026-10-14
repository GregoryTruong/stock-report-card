# Stock Report Card

A web app that grades any stock on Yahoo Finance (search by company name, including non-US
stocks like Aritzia on the Toronto exchange) from **A to F** on four things analysts look at
(**growth, profitability, valuation, and risk**) and compares it to the S&P 500.

Most student stock projects try to *predict* prices, which even professionals can't
do reliably. This project does what an analyst actually does instead: break a
company down, measure it against benchmarks, and explain the results in plain English.

## Features

- **Report card:** type a ticker (e.g. `AAPL`) and get an overall grade, four category
  grades, and a one-sentence explanation for each.
- **$10,000 growth chart:** what $10k invested in the stock would be worth today
  vs. the same amount in the S&P 500.
- **Drawdown chart:** how far the stock fell below its peak over time.
- **Compare stocks:** rank a list of tickers side by side.

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
src/ui.py            Colors, the scorecard table and chart styling
.streamlit/          App theme (colors and fonts)
tests/               Unit tests on made-up data with known answers
```

## Run it yourself

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `pytest`.

## Limitations and next steps

- The cutoffs are general rules of thumb. A software company and a grocery chain have
  very different "normal" margins, so a next step is grading against **industry peers**.
- Yahoo Finance data can be missing for some tickers (ETFs have no profit margin, for example).
- Good grades don't mean the price will go up. This is an analysis tool, not financial advice.
