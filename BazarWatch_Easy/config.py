"""All the fixed values of the app are kept here, so they are easy to change."""

from pathlib import Path

# The data folder is next to this file, so the app works from any folder.
BASE_FOLDER = Path(__file__).parent
DATA_FOLDER = BASE_FOLDER / "data"
REPORTS_FOLDER = BASE_FOLDER / "reports"

PRODUCTS_FILE = "products.json"
DATASET_FILE = "dataset_prices.csv"  # real prices from WFP (read only)
MY_PRICES_FILE = "my_prices.csv"     # prices the user adds in the app
BASKET_FILE = "basket.json"

CSV_HEADER = ("record_id", "product_id", "market", "date", "price")

# Tuples: these values never change while the app runs.
MARKETS = ("Dhaka Sadar", "Gazipur Sadar", "Narsingdi Sadar", "Manikganj Sadar")
UNITS = ("kg", "litre", "piece")
CATEGORIES = ("Grains", "Pulses", "Oil", "Grocery", "Vegetables", "Spices", "Protein")
ALERT_LEVELS = ("Normal", "Watch", "Spike")

# Alert limits. Perishable products (onion, potato, chilli) change price
# a lot, so they get looser limits.
Z_LIMIT = 2.0
PCT_LIMIT = 15.0
PERISHABLE_Z_LIMIT = 2.5
PERISHABLE_PCT_LIMIT = 25.0

# We need at least this many older prices before we trust a z-score.
MIN_HISTORY = 5

# The cheapest market and the basket use the prices of the last
# RECENT_DAYS days. We count back from the newest price we have,
# because the WFP data does not reach today.
RECENT_DAYS = 365

# Input limits
MAX_PRICE = 100000
MAX_QUANTITY = 1000
MAX_BUDGET = 1000000

# Budget status: up to 90% is fine, up to 100% is close, above is over.
BUDGET_CLOSE_PERCENT = 90
BUDGET_FULL_PERCENT = 100
