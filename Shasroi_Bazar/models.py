import config


class Product:
    def __init__(self, product_id: str, name: str, unit: str, category: str,
                 reference_price: float | None = None):
        self.product_id = product_id
        self.name = name
        self.unit = unit
        self.category = category
        self.reference_price = reference_price

    def is_perishable(self) -> bool:
        return False

    def spike_limits(self) -> tuple[float, float]:
        return config.Z_LIMIT, config.PCT_LIMIT

    def percent_over_reference(self, price: float) -> float | None:
        if self.reference_price is None or self.reference_price <= 0:
            return None
        return (price - self.reference_price) / self.reference_price * 100

    def label(self) -> str:
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
    def is_perishable(self) -> bool:
        return True

    def spike_limits(self) -> tuple[float, float]:
        return config.PERISHABLE_Z_LIMIT, config.PERISHABLE_PCT_LIMIT


def product_from_dict(data: dict) -> Product:
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
    def __init__(self, record_id: str, product_id: str, market: str, date: str,
                 price: float, source: str = "mine"):
        self.record_id = record_id
        self.product_id = product_id
        self.market = market
        self.date = date
        self.price = float(price)
        self.source = source

    def key(self) -> tuple[str, str, str]:
        return self.product_id, self.market, self.date

    def can_change(self) -> bool:
        return self.source == "mine"

    def to_row(self) -> list:
        return [self.record_id, self.product_id, self.market, self.date, self.price]
