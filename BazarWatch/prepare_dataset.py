import csv
import sys
from pathlib import Path

DATA_FOLDER = Path(__file__).parent / "data"
RAW_FILE = DATA_FOLDER / "raw" / "wfp_food_prices_bgd.csv"
OUTPUT_FILE = DATA_FOLDER / "dataset_prices.csv"

START_DATE = "2024-01-01"

KEEP_MARKETS = ("Dhaka Sadar", "Gazipur Sadar", "Narsingdi Sadar", "Manikganj Sadar")

COMMODITY_TO_PRODUCT = {
    "Rice (coarse)": "RICE",
    "Wheat flour": "ATTA",
    "Lentils (masur)": "DAL",
    "Oil (soybean, fortified)": "OIL",
    "Sugar": "SUGAR",
    "Onions (imported, China)": "ONION",
    "Potatoes (Holland, white)": "POTATO",
    "Garlic (imported, China)": "GARLIC",
    "Chili (green)": "CHILLI",
    "Eggs (brown)": "EGG",
}


def is_wanted(row: dict) -> bool:
    if row["pricetype"] != "Retail" or row["currency"] != "BDT":
        return False
    if row["market"] not in KEEP_MARKETS:
        return False
    if row["commodity"] not in COMMODITY_TO_PRODUCT:
        return False
    return row["date"] >= START_DATE


def main() -> int:
    raw_file = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_FILE
    try:
        with open(raw_file, encoding="utf-8", newline="") as file:
            raw_rows = list(csv.DictReader(file))
    except FileNotFoundError:
        print(f"Could not find {raw_file}. Download it first (see README.md).")
        return 1

    kept = []
    seen = set()
    skipped = 0
    for row in raw_rows:
        if not is_wanted(row):
            continue
        try:
            price = round(float(row["price"]), 2)
        except ValueError:
            skipped += 1
            continue

        product_id = COMMODITY_TO_PRODUCT[row["commodity"]]
        key = (product_id, row["market"], row["date"])
        if key in seen:
            continue
        seen.add(key)
        kept.append([product_id, row["market"], row["date"], price])

    kept.sort(key=lambda item: (item[2], item[0], item[1]))

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["record_id", "product_id", "market", "date", "price"])
        for number, (product_id, market, date, price) in enumerate(kept, start=1):
            writer.writerow([f"D{number:04d}", product_id, market, date, price])

    print(f"Read {len(raw_rows)} rows, kept {len(kept)}, skipped {skipped} bad prices.")
    print(f"Saved to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
