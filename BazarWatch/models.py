"""The classes that describe our data: products and price records."""

import config


class Product:
    """One item we track, for example rice or onion."""

    def __init__(self, product_id: str, name: str, unit: str, category: str,
                 reference_price: float | None = None):
        self.product_id = product_id
        self.name = name
        self.unit = unit
        self.category = category
        # The official (TCB) price. None means it has not been set yet.
        self.reference_price = reference_price

    def is_perishable(self) -> bool:
        return False

    def spike_limits(self) -> tuple[float, float]:
        """Return (z_limit, percent_limit) for this product."""
        return config.Z_LIMIT, config.PCT_LIMIT

    def percent_over_reference(self, price: float) -> float | None:
        """How many percent the price is above the reference price."""
        if self.reference_price is None or self.reference_price <= 0:
            return None
        return (price - self.reference_price) / self.reference_price * 100

    def label(self) -> str:
        """Text shown in the dropdowns, e.g. 'Onion (imported) [ONION]'."""
        return f"{self.name} [{self.product_id}]"

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "unit": self.unit,
            "category": self.category,
            "reference_price": self.reference_price,
            "perishable": self.is_perishable(),
        }


class PerishableProduct(Product):
    """A product that spoils fast. Same as Product, but with looser limits."""

    def is_perishable(self) -> bool:
        return True

    def spike_limits(self) -> tuple[float, float]:
        # Overrides the method of the parent class
        return config.PERISHABLE_Z_LIMIT, config.PERISHABLE_PCT_LIMIT


def product_from_dict(data: dict) -> Product:
    """Build the right kind of product from a dictionary (from products.json)."""
    reference = data.get("reference_price")
    if reference is not None:
        reference = float(reference)

    if data.get("perishable"):
        product_class = PerishableProduct
    else:
        product_class = Product

    return product_class(
        data["product_id"],
        data["name"],
        data.get("unit", "kg"),
        data.get("category", ""),
        reference,
    )


class PriceRecord:
    """One price: a product, at a market, on a date."""

    def __init__(self, record_id: str, product_id: str, market: str, date: str,
                 price: float, source: str = "mine"):
        self.record_id = record_id
        self.product_id = product_id
        self.market = market
        self.date = date            # text like "2026-07-15"
        self.price = float(price)
        # "dataset" = came from WFP, "mine" = added by the user
        self.source = source

    def key(self) -> tuple[str, str, str]:
        """Used to stop the same price being added twice."""
        return self.product_id, self.market, self.date

    def can_change(self) -> bool:
        """Only the user's own prices can be edited or deleted."""
        return self.source == "mine"

    def to_row(self) -> list:
        """One line of the CSV file."""
        return [self.record_id, self.product_id, self.market, self.date, self.price]
