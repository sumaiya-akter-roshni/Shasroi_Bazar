"""The calculations of the app.

NumPy does the maths (mean, median, min, max, standard deviation and the
dot product). The rules - Spike / Watch / Normal, which market is the
cheapest, budget status - are written in plain Python.
"""

from datetime import date, timedelta

import numpy as np

import config


def get_history(record, records: list) -> list:
    """Prices of the same product on or before this date, without the record itself."""
    history = []
    for other in records:
        if other is record:
            continue
        if other.product_id == record.product_id and other.date <= record.date:
            history.append(other.price)
    return history


def alert_level(record, product, records: list) -> tuple:
    """Decide if a price is Normal, Watch or Spike.

    Rule 1 (z-score): is the price far above the older prices?
    Rule 2 (reference): is the price far above the official price?
    Both rules true -> Spike, one true -> Watch, none -> Normal.

    Returns (level, z, pct). z or pct is None when it cannot be worked out.
    """
    z_limit, pct_limit = product.spike_limits()

    # Rule 1: z = (price - mean) / standard deviation
    z = None
    history = get_history(record, records)
    if len(history) >= config.MIN_HISTORY:
        prices = np.array(history)
        std = np.std(prices, ddof=1)  # ddof=1 -> sample standard deviation
        if std > 0:
            z = float((record.price - np.mean(prices)) / std)

    # Rule 2: percent above the reference price
    pct = product.percent_over_reference(record.price)

    z_hit = z is not None and z >= z_limit
    pct_hit = pct is not None and pct >= pct_limit

    if z_hit and pct_hit:
        level = "Spike"
    elif z_hit or pct_hit:
        level = "Watch"
    else:
        level = "Normal"
    return level, z, pct


def product_statistics(records: list) -> dict:
    """Count, mean, median, min, max and standard deviation of some prices."""
    if not records:
        return {"count": 0}
    prices = np.array([r.price for r in records])
    latest = max(records, key=lambda r: r.date)
    return {
        "count": len(prices),
        "mean": float(np.mean(prices)),
        "median": float(np.median(prices)),
        "min": float(np.min(prices)),
        "max": float(np.max(prices)),
        "std": float(np.std(prices, ddof=1)) if len(prices) > 1 else 0.0,
        "latest": latest.price,
        "latest_date": latest.date,
    }


def recent_records(records: list, days: int = config.RECENT_DAYS) -> list:
    """Records from the last `days` days, counting back from the newest record."""
    if not records:
        return []
    newest = max(r.date for r in records)
    start = (date.fromisoformat(newest) - timedelta(days=days)).isoformat()
    return [r for r in records if r.date > start]


def market_averages(product_id: str, records: list) -> dict:
    """Average price of one product in each market: {market: average}."""
    prices_by_market = {}
    for record in records:
        if record.product_id == product_id:
            prices_by_market.setdefault(record.market, []).append(record.price)

    averages = {}
    for market, prices in prices_by_market.items():
        averages[market] = float(np.mean(prices))
    return averages


def cheapest_market(product_id: str, records: list) -> tuple:
    """Return (market, average price) of the cheapest market, or (None, None)."""
    averages = market_averages(product_id, records)
    if not averages:
        return None, None
    best = min(averages, key=averages.get)
    return best, averages[best]


def basket_plan(items: dict, records: list) -> dict:
    """Work out what the basket costs.

    items is {product_id: quantity}. records should be the recent records.
    - total per market: only markets that sell every item, using np.dot
    - best single market: the market with the lowest total
    - split plan: buy each item at its own cheapest market
    """
    averages = {pid: market_averages(pid, records) for pid in items}
    priced = [pid for pid in items if averages[pid]]
    unpriced = [pid for pid in items if not averages[pid]]

    # Markets that have a price for every item = intersection of sets.
    # Start with all markets and keep only the ones that sell each item.
    common_markets = set()
    if priced:
        common_markets = set(config.MARKETS)
        for pid in priced:
            common_markets = common_markets & set(averages[pid])

    quantities = np.array([items[pid] for pid in priced])
    totals = {}
    for market in sorted(common_markets):
        prices = np.array([averages[pid][market] for pid in priced])
        totals[market] = float(np.dot(quantities, prices))  # sum of quantity * price

    best_market = min(totals, key=totals.get) if totals else None

    split_plan = {}
    split_total = 0.0
    for pid in priced:
        market, price = cheapest_market(pid, records)
        cost = items[pid] * price
        split_plan[pid] = (market, price, cost)
        split_total += cost

    saving = None
    if best_market is not None:
        saving = totals[best_market] - split_total

    return {
        "totals": totals,
        "best_market": best_market,
        "best_total": totals.get(best_market),
        "split_plan": split_plan,
        "split_total": split_total,
        "saving": saving,
        "unpriced": unpriced,
    }


def budget_percent(total: float, budget: float) -> float:
    """How much of the budget the total uses, in percent. 0 when there is no budget."""
    if budget <= 0:
        return 0.0
    return total / budget * 100


def budget_status(total: float, budget: float) -> tuple:
    """Return (status, message) comparing the basket total with the budget."""
    if budget <= 0:
        return "No budget", "Set a weekly budget to compare."

    percent = budget_percent(total, budget)
    if percent <= config.BUDGET_CLOSE_PERCENT:
        status = "Within budget"
    elif percent <= config.BUDGET_FULL_PERCENT:
        status = "Close to budget"
    else:
        status = "Over budget"

    if total > budget:
        message = f"Tk {total:.2f} of Tk {budget:.2f} - over by Tk {total - budget:.2f}"
    else:
        message = f"Tk {total:.2f} of Tk {budget:.2f} ({percent:.0f}% used)"
    return status, message
