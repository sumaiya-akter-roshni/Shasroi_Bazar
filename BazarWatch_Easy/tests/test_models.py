import unittest

import config
from models import PerishableProduct, PriceRecord, Product, product_from_dict


class TestModels(unittest.TestCase):
    def test_percent_over_reference(self):
        rice = Product("RICE", "Rice", "kg", "Grains", reference_price=50)
        self.assertAlmostEqual(rice.percent_over_reference(60), 20.0)

    def test_no_reference_price_gives_none(self):
        rice = Product("RICE", "Rice", "kg", "Grains")
        self.assertIsNone(rice.percent_over_reference(60))

    def test_perishable_product_has_looser_limits(self):
        rice = Product("RICE", "Rice", "kg", "Grains")
        onion = PerishableProduct("ONION", "Onion", "kg", "Vegetables")
        self.assertEqual(rice.spike_limits(), (config.Z_LIMIT, config.PCT_LIMIT))
        self.assertEqual(onion.spike_limits(),
                         (config.PERISHABLE_Z_LIMIT, config.PERISHABLE_PCT_LIMIT))

    def test_product_from_dict_picks_the_right_class(self):
        onion = product_from_dict({"product_id": "ONION", "name": "Onion", "perishable": True})
        rice = product_from_dict({"product_id": "RICE", "name": "Rice", "perishable": False})
        self.assertIsInstance(onion, PerishableProduct)
        self.assertNotIsInstance(rice, PerishableProduct)

    def test_to_dict_and_back_gives_the_same_product(self):
        onion = PerishableProduct("ONION", "Onion", "kg", "Vegetables", 45.0)
        again = product_from_dict(onion.to_dict())
        self.assertEqual(again.to_dict(), onion.to_dict())

    def test_price_record_key_and_source(self):
        mine = PriceRecord("M0001", "RICE", "Dhaka Sadar", "2026-11-01", 55)
        from_dataset = PriceRecord("D0001", "RICE", "Dhaka Sadar", "2026-01-15", 50, "dataset")
        self.assertEqual(mine.key(), ("RICE", "Dhaka Sadar", "2026-11-01"))
        self.assertTrue(mine.can_change())
        self.assertFalse(from_dataset.can_change())


if __name__ == "__main__":
    unittest.main()
