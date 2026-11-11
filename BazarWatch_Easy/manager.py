"""BazarManager: the middle part of the app.

The GUI never touches files or does calculations itself. It asks the
manager, and the manager uses validators.py, analytics.py and
file_handler.py to do the work.
"""

from datetime import date
from pathlib import Path

import analytics
import config
import file_handler
from models import PriceRecord
from validators import (
    BazarError,
    DuplicateRecordError,
    RecordNotFoundError,
    validate_budget,
    validate_choice,
    validate_date,
    validate_price,
    validate_quantity,
    validate_reference_price,
)


class BazarManager:
    def __init__(self, data_folder: Path = config.DATA_FOLDER,
                 reports_folder: Path = config.REPORTS_FOLDER):
        self.folder = Path(data_folder)
        self.reports_folder = Path(reports_folder)
        self.products = {}         # {product_id: Product}
        self.dataset_records = []  # real prices from WFP (read only)
        self.my_records = []       # prices added by the user
        self.basket = file_handler.empty_basket()
        self.problems = []         # file problems found while loading
        self.load_all()

    # ---------- loading and saving ----------

    def path(self, file_name: str) -> Path:
        return self.folder / file_name

    def load_all(self) -> None:
        """Read every data file. Problems are kept in self.problems."""
        self.problems = []
        try:
            self.folder.mkdir(exist_ok=True)
        except OSError as error:
            self.problems.append(f"Could not create the data folder: {error}")

        self.products, problems = file_handler.load_products(self.path(config.PRODUCTS_FILE))
        self.problems.extend(problems)

        known_ids = set(self.products)
        self.dataset_records, problems = file_handler.load_prices(
            self.path(config.DATASET_FILE), "dataset", known_ids)
        self.problems.extend(problems)

        self.my_records, problems = file_handler.load_prices(
            self.path(config.MY_PRICES_FILE), "mine", known_ids)
        self.problems.extend(problems)

        self.basket, problems = file_handler.load_basket(self.path(config.BASKET_FILE))
        self.problems.extend(problems)

    def save_my_prices(self) -> None:
        try:
            file_handler.save_prices(self.path(config.MY_PRICES_FILE), self.my_records)
        except OSError as error:
            raise BazarError(f"Could not save your prices: {error}") from error

    def save_products(self) -> None:
        try:
            file_handler.save_products(self.path(config.PRODUCTS_FILE), self.products)
        except OSError as error:
            raise BazarError(f"Could not save the products: {error}") from error

    def save_basket(self) -> None:
        try:
            file_handler.save_basket(self.path(config.BASKET_FILE), self.basket)
        except OSError as error:
            raise BazarError(f"Could not save the basket: {error}") from error

    # ---------- products ----------

    def get_product(self, product_id: str):
        if product_id not in self.products:
            raise RecordNotFoundError(f"There is no product '{product_id}'.")
        return self.products[product_id]

    def product_labels(self) -> dict:
        """{label shown in a dropdown: product_id}, sorted by name."""
        products = sorted(self.products.values(), key=lambda p: p.name)
        return {product.label(): product.product_id for product in products}

    def product_name(self, product_id: str) -> str:
        product = self.products.get(product_id)
        return product.name if product else product_id

    def set_reference_price(self, product_id: str, text) -> None:
        product = self.get_product(product_id)
        product.reference_price = validate_reference_price(text)
        self.save_products()

    # ---------- price records ----------

    def all_records(self) -> list:
        return self.dataset_records + self.my_records

    def next_record_id(self) -> str:
        numbers = [int(r.record_id[1:]) for r in self.my_records if r.record_id[1:].isdigit()]
        return f"M{max(numbers, default=0) + 1:04d}"

    def check_duplicate(self, key: tuple, skip_id: str | None = None) -> None:
        """Stop the user adding the same product, market and date twice."""
        used_keys = {r.key() for r in self.my_records if r.record_id != skip_id}
        if key in used_keys:
            raise DuplicateRecordError(
                "You already added a price for this product at this market on this date.")

    def add_price(self, product_id: str, market: str, day: str, price_text) -> PriceRecord:
        self.get_product(product_id)
        market = validate_choice(market, config.MARKETS, "market")
        day = validate_date(day)
        price = validate_price(price_text)
        self.check_duplicate((product_id, market, day))

        record = PriceRecord(self.next_record_id(), product_id, market, day, price, "mine")
        self.my_records.append(record)
        self.save_my_prices()
        return record

    def find_record(self, record_id: str) -> PriceRecord:
        for record in self.all_records():
            if record.record_id == record_id:
                return record
        raise RecordNotFoundError(f"Record {record_id} was not found.")

    def update_price(self, record_id: str, market: str, day: str, price_text) -> PriceRecord:
        record = self.find_record(record_id)
        if not record.can_change():
            raise BazarError("Prices from the dataset cannot be changed.")

        # Check everything first, so a wrong value changes nothing
        market = validate_choice(market, config.MARKETS, "market")
        day = validate_date(day)
        price = validate_price(price_text)
        self.check_duplicate((record.product_id, market, day), skip_id=record_id)

        record.market = market
        record.date = day
        record.price = price
        self.save_my_prices()
        return record

    def delete_price(self, record_id: str) -> None:
        record = self.find_record(record_id)
        if not record.can_change():
            raise BazarError("Prices from the dataset cannot be deleted.")
        self.my_records.remove(record)
        self.save_my_prices()

    def search(self, text: str = "", product_id: str | None = None) -> list:
        """Find records by product, market, date or ID. Empty text means all."""
        text = text.strip().lower()
        results = []
        for record in self.all_records():
            if product_id and record.product_id != product_id:
                continue
            words = (f"{record.record_id} {record.product_id} "
                     f"{self.product_name(record.product_id)} {record.market} {record.date}")
            if text in words.lower():
                results.append(record)
        results.sort(key=lambda r: r.date, reverse=True)  # newest first
        return results

    # ---------- analysis ----------

    def alert_for(self, record: PriceRecord) -> tuple:
        product = self.get_product(record.product_id)
        same_product = [r for r in self.all_records() if r.product_id == record.product_id]
        return analytics.alert_level(record, product, same_product)

    def all_alerts(self) -> dict:
        """{record_id: (level, z, pct)} for every record."""
        # Group the records by product first, so each alert only looks
        # at the prices of its own product.
        by_product = {}
        for record in self.all_records():
            by_product.setdefault(record.product_id, []).append(record)

        alerts = {}
        for product_id, records in by_product.items():
            product = self.products[product_id]
            for record in records:
                alerts[record.record_id] = analytics.alert_level(record, product, records)
        return alerts

    def alert_counts(self) -> dict:
        """How many recent prices are Normal, Watch and Spike: {level: count}."""
        alerts = self.all_alerts()
        counts = dict.fromkeys(config.ALERT_LEVELS, 0)
        for record in self.recent_records():
            level = alerts[record.record_id][0]
            counts[level] += 1
        return counts

    def recent_records(self) -> list:
        return analytics.recent_records(self.all_records())

    def statistics(self) -> list:
        """One row of numbers for every product."""
        recent = self.recent_records()
        rows = []
        for product in sorted(self.products.values(), key=lambda p: p.name):
            records = [r for r in self.all_records() if r.product_id == product.product_id]
            stats = analytics.product_statistics(records)
            stats["product"] = product
            stats["cheapest"] = analytics.cheapest_market(product.product_id, recent)
            rows.append(stats)
        return rows

    # ---------- basket ----------

    def set_basket_item(self, product_id: str, quantity_text) -> None:
        self.get_product(product_id)
        self.basket["items"][product_id] = validate_quantity(quantity_text)
        self.save_basket()

    def remove_basket_item(self, product_id: str) -> None:
        if product_id not in self.basket["items"]:
            raise RecordNotFoundError("That product is not in your basket.")
        del self.basket["items"][product_id]
        self.save_basket()

    def set_budget(self, budget_text) -> None:
        self.basket["budget"] = validate_budget(budget_text)
        self.save_basket()

    def basket_plan(self) -> dict:
        plan = analytics.basket_plan(self.basket["items"], self.recent_records())
        budget = self.basket["budget"]
        plan["status"] = analytics.budget_status(plan["split_total"], budget)
        plan["budget_percent"] = analytics.budget_percent(plan["split_total"], budget)
        return plan

    # ---------- report ----------

    def build_report(self) -> str:
        lines = []
        recent = self.recent_records()
        newest = max((r.date for r in recent), default="-")

        lines.append("BazarWatch BD - Price Report")
        lines.append("=" * 60)
        lines.append(f"Made on      : {date.today().isoformat()}")
        lines.append(f"Dataset      : {len(self.dataset_records)} prices from WFP")
        lines.append(f"My prices    : {len(self.my_records)}")
        lines.append(f"Recent window: last {config.RECENT_DAYS} days up to {newest}")
        lines.append("")

        lines.append("PRODUCT SUMMARY")
        lines.append("-" * 60)
        for row in self.statistics():
            product = row["product"]
            if row["count"] == 0:
                lines.append(f"{product.name}: no prices yet")
                continue
            market, average = row["cheapest"]
            cheapest = f"{market} (Tk {average:.2f})" if market else "no recent data"
            lines.append(f"{product.name} - per {product.unit}")
            lines.append(f"   average Tk {row['mean']:.2f}, min Tk {row['min']:.2f}, "
                         f"max Tk {row['max']:.2f}, latest Tk {row['latest']:.2f}")
            lines.append(f"   cheapest market: {cheapest}")
        lines.append("")

        lines.append("SPIKE AND WATCH PRICES (recent window)")
        lines.append("-" * 60)
        alerts = self.all_alerts()
        found = 0
        for record in sorted(recent, key=lambda r: r.date):
            level, z, pct = alerts[record.record_id]
            if level == "Normal":
                continue
            found += 1
            z_text = f"z={z:.2f}" if z is not None else "z=-"
            pct_text = f"{pct:+.1f}% vs reference" if pct is not None else "no reference"
            lines.append(f"{level:6} {record.date} {self.product_name(record.product_id):22} "
                         f"{record.market:16} Tk {record.price:.2f} ({z_text}, {pct_text})")
        if found == 0:
            lines.append("No unusual prices.")
        lines.append("")

        plan = self.basket_plan()
        status, message = plan["status"]
        lines.append("MY BASKET")
        lines.append("-" * 60)
        lines.append(f"Split plan total: Tk {plan['split_total']:.2f}")
        if plan["best_market"]:
            lines.append(f"Best single market: {plan['best_market']} "
                         f"(Tk {plan['best_total']:.2f})")
        lines.append(f"Budget: {status} - {message}")
        lines.append("")
        lines.append("Price data: World Food Programme (WFP), via HDX, licence CC BY-IGO.")
        return "\n".join(lines) + "\n"

    def save_report(self) -> Path:
        try:
            return file_handler.save_report(self.build_report(), self.reports_folder)
        except OSError as error:
            raise BazarError(f"Could not save the report: {error}") from error
