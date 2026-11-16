import unittest

import analytics
from models import PerishableProduct, PriceRecord, Product


def make_records(product_id, prices, market="Dhaka Sadar"):
    """One record per price, one month apart, starting in January 2026."""
    records = []
    for month, price in enumerate(prices, start=1):
        records.append(PriceRecord(f"T{month:03d}", product_id, market,
                                   f"2026-{month:02d}-15", price, "dataset"))
    return records


class TestAlertLevel(unittest.TestCase):
    def setUp(self):
        # Older prices: 40, 42, 38, 41, 39 -> mean 40, std about 1.58
        self.history = make_records("RICE", [40, 42, 38, 41, 39])

    def check(self, product, new_price):
        new = PriceRecord("M0001", product.product_id, "Dhaka Sadar", "2026-07-15", new_price)
        return analytics.alert_level(new, product, self.history + [new])

    def test_history_leaves_out_the_record_itself_and_later_dates(self):
        first = self.history[0]
        self.assertEqual(analytics.get_history(first, self.history), [])
        self.assertEqual(len(analytics.get_history(self.history[-1], self.history)), 4)

    def test_spike_when_both_rules_fire(self):
        rice = Product("RICE", "Rice", "kg", "Grains", reference_price=45)
        level, z, pct = self.check(rice, 60)
        self.assertEqual(level, "Spike")
        self.assertGreater(z, 2)
        self.assertGreater(pct, 15)

    def test_watch_when_only_the_z_rule_fires(self):
        rice = Product("RICE", "Rice", "kg", "Grains")  # no reference price
        level, z, pct = self.check(rice, 60)
        self.assertEqual(level, "Watch")
        self.assertIsNone(pct)

    def test_normal_price(self):
        rice = Product("RICE", "Rice", "kg", "Grains", reference_price=45)
        level, _, _ = self.check(rice, 41)
        self.assertEqual(level, "Normal")

    def test_no_z_score_with_too_little_history(self):
        rice = Product("RICE", "Rice", "kg", "Grains")
        self.history = self.history[:3]
        level, z, _ = self.check(rice, 60)
        self.assertIsNone(z)
        self.assertEqual(level, "Normal")

    def test_perishable_allows_a_bigger_jump(self):
        # z is about 2.2 here: a Watch for rice, but fine for a perishable
        normal = Product("RICE", "Rice", "kg", "Grains")
        perishable = PerishableProduct("RICE", "Rice", "kg", "Grains")
        self.assertEqual(self.check(normal, 43.5)[0], "Watch")
        self.assertEqual(self.check(perishable, 43.5)[0], "Normal")


class TestStatisticsAndMarkets(unittest.TestCase):
    def test_product_statistics(self):
        stats = analytics.product_statistics(make_records("RICE", [10, 20, 30]))
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["mean"], 20)
        self.assertEqual(stats["median"], 20)
        self.assertEqual(stats["min"], 10)
        self.assertEqual(stats["max"], 30)
        self.assertEqual(stats["latest"], 30)

    def test_cheapest_market_has_the_lowest_average(self):
        records = make_records("RICE", [50, 52], "Dhaka Sadar")
        records += make_records("RICE", [48, 49], "Gazipur Sadar")
        self.assertEqual(analytics.cheapest_market("RICE", records), ("Gazipur Sadar", 48.5))

    def test_no_data_gives_no_market(self):
        self.assertEqual(analytics.cheapest_market("RICE", []), (None, None))

    def test_recent_records_drops_old_prices(self):
        old = PriceRecord("A", "RICE", "Dhaka Sadar", "2024-01-15", 40)
        new = PriceRecord("B", "RICE", "Dhaka Sadar", "2026-01-15", 50)
        self.assertEqual(analytics.recent_records([old, new], days=365), [new])


class TestBasket(unittest.TestCase):
    def setUp(self):
        self.records = [
            PriceRecord("1", "RICE", "Dhaka Sadar", "2026-05-15", 60),
            PriceRecord("2", "OIL", "Dhaka Sadar", "2026-05-15", 190),
            PriceRecord("3", "RICE", "Gazipur Sadar", "2026-05-15", 65),
            PriceRecord("4", "OIL", "Gazipur Sadar", "2026-05-15", 185),
        ]

    def test_totals_best_market_and_saving(self):
        plan = analytics.basket_plan({"RICE": 2, "OIL": 1}, self.records)
        self.assertEqual(plan["totals"], {"Dhaka Sadar": 310, "Gazipur Sadar": 315})
        self.assertEqual(plan["best_market"], "Dhaka Sadar")
        self.assertEqual(plan["split_total"], 305)  # rice at Dhaka, oil at Gazipur
        self.assertEqual(plan["saving"], 5)

    def test_market_without_every_item_is_left_out(self):
        self.records.pop()  # Gazipur has no oil now
        plan = analytics.basket_plan({"RICE": 2, "OIL": 1}, self.records)
        self.assertEqual(list(plan["totals"]), ["Dhaka Sadar"])

    def test_item_with_no_price_is_listed(self):
        plan = analytics.basket_plan({"RICE": 1, "SUGAR": 1}, self.records)
        self.assertEqual(plan["unpriced"], ["SUGAR"])

    def test_budget_status(self):
        self.assertEqual(analytics.budget_status(80, 100)[0], "Within budget")
        self.assertEqual(analytics.budget_status(95, 100)[0], "Close to budget")
        self.assertEqual(analytics.budget_status(120, 100)[0], "Over budget")
        self.assertEqual(analytics.budget_status(50, 0)[0], "No budget")

    def test_budget_percent(self):
        self.assertEqual(analytics.budget_percent(50, 200), 25)
        self.assertEqual(analytics.budget_percent(50, 0), 0)


if __name__ == "__main__":
    unittest.main()
