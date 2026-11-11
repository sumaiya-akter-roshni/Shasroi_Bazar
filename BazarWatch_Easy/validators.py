"""Our own error types and the functions that check user input."""

from datetime import date

import config


class BazarError(Exception):
    """Parent of all our errors. The GUI catches this one and shows the message."""


class ValidationError(BazarError):
    """The user typed something wrong (empty, not a number, out of range)."""


class DuplicateRecordError(BazarError):
    """The same price was already added."""


class RecordNotFoundError(BazarError):
    """We could not find the record or product that was asked for."""


def to_number(text, field_name: str) -> float:
    """Turn the text from an entry box into a number."""
    if text is None or str(text).strip() == "":
        raise ValidationError(f"{field_name} is required.")
    try:
        return float(text)
    except ValueError:
        raise ValidationError(f"{field_name} must be a number.") from None


def validate_price(text) -> float:
    price = to_number(text, "Price")
    if price <= 0:
        raise ValidationError("Price must be more than 0.")
    if price > config.MAX_PRICE:
        raise ValidationError(f"Price cannot be more than {config.MAX_PRICE}.")
    return round(price, 2)


def validate_quantity(text) -> float:
    quantity = to_number(text, "Quantity")
    if quantity <= 0:
        raise ValidationError("Quantity must be more than 0.")
    if quantity > config.MAX_QUANTITY:
        raise ValidationError(f"Quantity cannot be more than {config.MAX_QUANTITY}.")
    return quantity


def validate_budget(text) -> float:
    budget = to_number(text, "Budget")
    if budget < 0:
        raise ValidationError("Budget cannot be negative.")
    if budget > config.MAX_BUDGET:
        raise ValidationError(f"Budget cannot be more than {config.MAX_BUDGET}.")
    return budget


def validate_reference_price(text) -> float | None:
    """An empty box means 'no reference price', which is allowed."""
    if text is None or str(text).strip() == "":
        return None
    return validate_price(text)


def validate_date(text) -> str:
    """The date must look like 2026-11-07 and must not be in the future."""
    text = str(text).strip()
    if text == "":
        raise ValidationError("Date is required.")
    try:
        day = date.fromisoformat(text)
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format.") from None
    if day > date.today():
        raise ValidationError("Date cannot be in the future.")
    return day.isoformat()


def validate_choice(value: str, options, field_name: str) -> str:
    """The value must be one of the allowed options (used for markets)."""
    if value not in options:
        raise ValidationError(f"Please choose a valid {field_name}.")
    return value
