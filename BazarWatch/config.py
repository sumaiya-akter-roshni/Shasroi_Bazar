from pathlib import Path

BASE_FOLDER = Path(__file__).parent
DATA_FOLDER = BASE_FOLDER / "data"
REPORTS_FOLDER = BASE_FOLDER / "reports"

PRODUCTS_FILE = "products.json"
DATASET_FILE = "dataset_prices.csv"
MY_PRICES_FILE = "my_prices.csv"
BASKET_FILE = "basket.json"

CSV_HEADER = ("record_id", "product_id", "market", "date", "price")

MARKETS = ("Dhaka Sadar", "Gazipur Sadar", "Narsingdi Sadar", "Manikganj Sadar")
UNITS = ("kg", "litre", "piece")
CATEGORIES = ("Grains", "Pulses", "Oil", "Grocery", "Vegetables", "Spices", "Protein")
ALERT_LEVELS = ("Normal", "Watch", "Spike")

Z_LIMIT = 2.0
PCT_LIMIT = 15.0
PERISHABLE_Z_LIMIT = 2.5
PERISHABLE_PCT_LIMIT = 25.0

MIN_HISTORY = 5

RECENT_DAYS = 365

MAX_PRICE = 100000
MAX_QUANTITY = 1000
MAX_BUDGET = 1000000

BUDGET_CLOSE_PERCENT = 90
BUDGET_FULL_PERCENT = 100
