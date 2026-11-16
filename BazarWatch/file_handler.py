"""Reading and writing the data files (JSON, CSV and TXT).

Every function here handles its own file errors, so a missing or broken
file never closes the app. Problems are returned as a list of messages
and the GUI shows them to the user.
"""

import csv
import json
from datetime import date
from pathlib import Path

import config
from models import PriceRecord, product_from_dict


# ---------- products.json ----------

def load_products(path: Path) -> tuple[dict, list]:
    """Return ({product_id: Product}, problems)."""
    problems = []
    products = {}
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        problems.append(f"{path.name} was not found, so there are no products.")
        return products, problems
    except json.JSONDecodeError:
        problems.append(f"{path.name} is broken (not valid JSON), so there are no products.")
        return products, problems

    for item in data:
        try:
            product = product_from_dict(item)
        except (KeyError, TypeError, ValueError):
            problems.append(f"{path.name}: skipped a product with missing or wrong values.")
            continue
        products[product.product_id] = product
    return products, problems


def save_products(path: Path, products: dict) -> None:
    data = [product.to_dict() for product in products.values()]
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


# ---------- price CSV files ----------

def check_row(row: list, known_products: set, seen_ids: set) -> str | None:
    """Return why a CSV row is bad, or None if the row is fine."""
    if len(row) != len(config.CSV_HEADER):
        return f"expected {len(config.CSV_HEADER)} values but found {len(row)}"

    record_id, product_id, market, day, price = row
    if record_id.strip() == "":
        return "record ID is empty"
    if record_id in seen_ids:
        return f"record ID {record_id} is used twice"
    if product_id not in known_products:
        return f"unknown product '{product_id}'"
    if market.strip() == "":
        return "market is empty"
    try:
        date.fromisoformat(day)
    except ValueError:
        return f"date '{day}' is not YYYY-MM-DD"
    try:
        if float(price) <= 0:
            return f"price '{price}' is not more than 0"
    except ValueError:
        return f"price '{price}' is not a number"
    return None


def load_prices(path: Path, source: str, known_products: set) -> tuple[list, list]:
    """Read a price CSV file. Bad rows are skipped and reported.

    Returns (list of PriceRecord, problems).
    """
    records = []
    problems = []
    seen_ids = set()  # a set makes "have we seen this ID?" fast and simple

    try:
        with open(path, encoding="utf-8", newline="") as file:
            rows = list(csv.reader(file))
    except FileNotFoundError:
        if source == "mine":
            # First run: start with an empty file
            save_prices(path, [])
        else:
            problems.append(f"{path.name} was not found, so only your own prices are used.")
        return records, problems

    for line_number, row in enumerate(rows[1:], start=2):  # line 1 is the header
        if not row:
            continue  # ignore empty lines
        reason = check_row(row, known_products, seen_ids)
        if reason:
            problems.append(f"{path.name} line {line_number}: {reason}")
            continue
        record = PriceRecord(row[0], row[1], row[2], row[3], float(row[4]), source)
        seen_ids.add(record.record_id)
        records.append(record)

    return records, problems


def save_prices(path: Path, records: list) -> None:
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(config.CSV_HEADER)
        for record in records:
            writer.writerow(record.to_row())


# ---------- basket.json ----------

def empty_basket() -> dict:
    return {"budget": 0.0, "items": {}}


def load_basket(path: Path) -> tuple[dict, list]:
    """Return (basket, problems). The basket is {"budget": ..., "items": {id: qty}}."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        basket = {
            "budget": float(data.get("budget", 0)),
            "items": {pid: float(qty) for pid, qty in data.get("items", {}).items()},
        }
        return basket, []
    except FileNotFoundError:
        return empty_basket(), []
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
        return empty_basket(), [f"{path.name} is broken, so the basket starts empty."]


def save_basket(path: Path, basket: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(basket, file, indent=2)


# ---------- report (.txt) ----------

def save_report(text: str, folder: Path) -> Path:
    """Save the report as reports/report_YYYY-MM-DD.txt and return the path."""
    folder.mkdir(exist_ok=True)
    path = folder / f"report_{date.today().isoformat()}.txt"
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return path
