"""Turns raw metrics into 0-100 scores and A-F letter grades."""

import math

# Each rule is: (label, metric key, worst value, best value, display format).
# A metric at its "worst" value scores 0, at its "best" scores 100, and values
# in between are scaled in a straight line. When worst > best (like P/E),
# lower numbers are better. The cutoffs are rough rules of thumb from common
# analyst benchmarks, not official standards.
CATEGORIES = {
    "Growth": [
        ("Revenue growth (yearly)", "revenue_growth", 0.00, 0.25, "pct"),
        ("Earnings growth (yearly)", "earnings_growth", -0.10, 0.30, "pct"),
    ],
    "Profitability": [
        ("Profit margin", "profit_margin", 0.00, 0.25, "pct"),
        ("Return on equity", "return_on_equity", 0.00, 0.30, "pct"),
    ],
    "Valuation": [
        ("P/E ratio (past 12 months)", "trailing_pe", 40, 12, "ratio"),
        ("P/E ratio (next 12 months)", "forward_pe", 35, 10, "ratio"),
        ("Price-to-sales", "price_to_sales", 15, 1, "ratio"),
    ],
    "Risk": [
        ("Volatility (yearly)", "volatility", 0.60, 0.15, "pct"),
        ("Worst drop from peak", "max_drawdown", -0.70, -0.15, "pct"),
        ("Beta vs S&P 500", "beta", 2.0, 0.8, "ratio"),
    ],
}

# One plain-English sentence per category for a high, middle, or low score.
SUMMARIES = {
    "Growth": (
        "Sales and profits are growing quickly.",
        "Growing at a moderate pace.",
        "Growth is slow, or the business is shrinking.",
    ),
    "Profitability": (
        "Keeps a large share of its sales as profit.",
        "Decently profitable.",
        "Keeps little of its sales as profit, or is losing money.",
    ),
    "Valuation": (
        "The price looks cheap compared to what the company earns.",
        "The price looks fair compared to what the company earns.",
        "Expensive: investors are paying a lot for each dollar of profit, "
        "usually because they expect big future growth.",
    ),
    "Risk": (
        "The price has been relatively steady.",
        "A normal amount of ups and downs.",
        "Big price swings and deep drops. Expect a bumpy ride.",
    ),
}


def score_metric(value, worst, best):
    """Scale a value to 0-100 between its worst and best cutoffs."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if math.isinf(value):
        return 0.0
    score = (value - worst) / (best - worst) * 100
    return max(0.0, min(100.0, score))


def letter_grade(score):
    if score is None:
        return "N/A"
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def summary_for(category, score):
    if score is None:
        return "Yahoo Finance doesn't have this data (common for funds and ETFs)."
    high, mid, low = SUMMARIES[category]
    if score >= 65:
        return high
    if score >= 40:
        return mid
    return low


def format_value(value, kind):
    if value is None:
        return "No data"
    if math.isinf(value):
        return "N/A (losing money)"
    return f"{value:.1%}" if kind == "pct" else f"{value:.2f}"


def _average(scores):
    scores = [s for s in scores if s is not None]
    return sum(scores) / len(scores) if scores else None


def build_report_card(metrics: dict) -> dict:
    """Score every category and the stock overall.

    Returns {"categories": {name: {...}}, "overall_score": float, "overall_grade": str}.
    """
    categories = {}
    for name, rules in CATEGORIES.items():
        details = []
        for label, key, worst, best, kind in rules:
            value = metrics.get(key)
            details.append(
                {
                    "Metric": label,
                    "Value": format_value(value, kind),
                    "Score": score_metric(value, worst, best),
                }
            )
        category_score = _average(d["Score"] for d in details)
        categories[name] = {
            "score": category_score,
            "grade": letter_grade(category_score),
            "summary": summary_for(name, category_score),
            "details": details,
        }

    overall_score = _average(c["score"] for c in categories.values())
    return {
        "categories": categories,
        "overall_score": overall_score,
        "overall_grade": letter_grade(overall_score),
    }
