"""Small helpers shared by the tests: a temporary data folder with test data."""

import json
import tempfile
from pathlib import Path

TEST_PRODUCTS = [
    {"product_id": "RICE", "name": "Rice", "unit": "kg", "category": "Grains",
     "reference_price": 50.0, "perishable": False},
    {"product_id": "ONION", "name": "Onion", "unit": "kg", "category": "Vegetables",
     "reference_price": None, "perishable": True},
    {"product_id": "OIL", "name": "Soybean oil", "unit": "litre", "category": "Oil",
     "reference_price": None, "perishable": False},
]

TEST_DATASET = """record_id,product_id,market,date,price
D0001,RICE,Dhaka Sadar,2026-01-15,50
D0002,RICE,Gazipur Sadar,2026-02-15,52
D0003,RICE,Dhaka Sadar,2026-03-15,48
D0004,RICE,Gazipur Sadar,2026-04-15,51
D0005,RICE,Dhaka Sadar,2026-05-15,49
D0006,OIL,Dhaka Sadar,2026-05-15,190
D0007,OIL,Gazipur Sadar,2026-05-15,185
"""


def make_data_folder() -> tuple[tempfile.TemporaryDirectory, Path]:
    """Create a temporary data folder. Call .cleanup() on the first value at the end."""
    temp = tempfile.TemporaryDirectory()
    folder = Path(temp.name)
    (folder / "products.json").write_text(json.dumps(TEST_PRODUCTS), encoding="utf-8")
    (folder / "dataset_prices.csv").write_text(TEST_DATASET, encoding="utf-8")
    return temp, folder
