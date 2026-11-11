import unittest
from datetime import date, timedelta

from validators import (
    BazarError,
    ValidationError,
    validate_budget,
    validate_choice,
    validate_date,
    validate_price,
    validate_quantity,
    validate_reference_price,
)


class TestValidators(unittest.TestCase):
    def test_good_price_is_accepted(self):
        self.assertEqual(validate_price("55.5"), 55.5)

    def test_bad_prices_are_refused(self):
        for bad in ["", "   ", "abc", "0", "-5", "200000"]:
            with self.assertRaises(ValidationError):
                validate_price(bad)

    def test_date_must_be_in_the_right_format(self):
        with self.assertRaises(ValidationError):
            validate_date("07-11-2026")

    def test_future_date_is_refused(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        with self.assertRaises(ValidationError):
            validate_date(tomorrow)

    def test_today_is_accepted(self):
        today = date.today().isoformat()
        self.assertEqual(validate_date(today), today)

    def test_quantity_and_budget_limits(self):
        with self.assertRaises(ValidationError):
            validate_quantity("0")
        with self.assertRaises(ValidationError):
            validate_budget("-100")
        self.assertEqual(validate_budget("0"), 0)

    def test_empty_reference_price_means_none(self):
        self.assertIsNone(validate_reference_price(""))
        self.assertEqual(validate_reference_price("60"), 60)

    def test_unknown_market_is_refused(self):
        with self.assertRaises(ValidationError):
            validate_choice("Some Market", ("Dhaka Sadar",), "market")

    def test_all_errors_come_from_bazar_error(self):
        self.assertTrue(issubclass(ValidationError, BazarError))


if __name__ == "__main__":
    unittest.main()
