import unittest
from pathlib import Path

from manager import BazarManager
from tests.helpers import make_data_folder
from validators import BazarError, DuplicateRecordError, RecordNotFoundError, ValidationError


class ManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.temp, self.folder = make_data_folder()
        self.manager = BazarManager(self.folder, self.folder / "reports")

    def tearDown(self):
        self.temp.cleanup()

    def reload(self) -> BazarManager:
        return BazarManager(self.folder, self.folder / "reports")


class TestLoading(ManagerTestCase):
    def test_everything_loads_without_problems(self):
        self.assertEqual(len(self.manager.products), 3)
        self.assertEqual(len(self.manager.dataset_records), 7)
        self.assertEqual(self.manager.problems, [])

    def test_missing_my_prices_file_is_created(self):
        self.assertTrue((self.folder / "my_prices.csv").exists())

    def test_bad_csv_rows_are_skipped_and_reported(self):
        with open(self.folder / "dataset_prices.csv", "a", encoding="utf-8") as file:
            file.write("D0008,RICE,Dhaka Sadar,2026-06-15,abc\n")
            file.write("D0009,MANGO,Dhaka Sadar,2026-06-15,100\n")
            file.write("D0010,RICE,Dhaka Sadar,15-06-2026,50\n")
        manager = self.reload()
        self.assertEqual(len(manager.dataset_records), 7)
        self.assertEqual(len(manager.problems), 3)

    def test_broken_basket_file_does_not_stop_the_app(self):
        (self.folder / "basket.json").write_text("{ not json", encoding="utf-8")
        manager = self.reload()
        self.assertEqual(manager.basket["items"], {})
        self.assertEqual(len(manager.problems), 1)

    def test_missing_dataset_is_reported(self):
        (self.folder / "dataset_prices.csv").unlink()
        manager = self.reload()
        self.assertEqual(manager.dataset_records, [])
        self.assertEqual(len(manager.problems), 1)


class TestPrices(ManagerTestCase):
    def test_added_price_is_saved_and_survives_a_restart(self):
        record = self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "55")
        self.assertEqual(record.record_id, "M0001")
        manager = self.reload()
        self.assertEqual(len(manager.my_records), 1)
        self.assertEqual(manager.my_records[0].price, 55)

    def test_same_price_twice_is_refused(self):
        self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "55")
        with self.assertRaises(DuplicateRecordError):
            self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "56")

    def test_wrong_input_is_refused_and_nothing_is_saved(self):
        with self.assertRaises(ValidationError):
            self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "abc")
        with self.assertRaises(ValidationError):
            self.manager.add_price("RICE", "Unknown Market", "2026-06-15", "55")
        with self.assertRaises(RecordNotFoundError):
            self.manager.add_price("MANGO", "Dhaka Sadar", "2026-06-15", "55")
        self.assertEqual(self.reload().my_records, [])

    def test_own_price_can_be_edited(self):
        record = self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "55")
        self.manager.update_price(record.record_id, "Gazipur Sadar", "2026-06-16", "57")
        saved = self.reload().find_record(record.record_id)
        self.assertEqual(saved.market, "Gazipur Sadar")
        self.assertEqual(saved.date, "2026-06-16")
        self.assertEqual(saved.price, 57)

    def test_a_refused_edit_changes_nothing(self):
        record = self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "55")
        with self.assertRaises(ValidationError):
            self.manager.update_price(record.record_id, "Gazipur Sadar", "2026-06-16", "-1")
        self.assertEqual(record.market, "Dhaka Sadar")
        self.assertEqual(record.price, 55)

    def test_own_price_can_be_deleted(self):
        record = self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "55")
        self.manager.delete_price(record.record_id)
        self.assertEqual(self.reload().my_records, [])

    def test_dataset_prices_cannot_be_changed(self):
        with self.assertRaises(BazarError):
            self.manager.update_price("D0001", "Dhaka Sadar", "2026-01-15", "99")
        with self.assertRaises(BazarError):
            self.manager.delete_price("D0001")

    def test_missing_record_is_reported(self):
        with self.assertRaises(RecordNotFoundError):
            self.manager.find_record("M9999")

    def test_search(self):
        self.assertEqual(len(self.manager.search("oil")), 2)
        self.assertEqual(len(self.manager.search("", "RICE")), 5)
        self.assertEqual(self.manager.search("nothing like this"), [])


class TestAnalysisAndBasket(ManagerTestCase):
    def test_reference_price_makes_a_spike(self):
        self.manager.set_reference_price("RICE", "")
        record = self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "70")
        self.assertEqual(self.manager.alert_for(record)[0], "Watch")
        self.manager.set_reference_price("RICE", "50")
        self.assertEqual(self.manager.alert_for(record)[0], "Spike")
        self.assertEqual(self.reload().products["RICE"].reference_price, 50)

    def test_alert_counts(self):
        self.manager.add_price("RICE", "Dhaka Sadar", "2026-06-15", "70")
        counts = self.manager.alert_counts()
        self.assertEqual(counts, {"Normal": 7, "Watch": 0, "Spike": 1})

    def test_basket_and_budget_are_saved(self):
        self.manager.set_basket_item("RICE", "3")
        self.manager.set_basket_item("OIL", "1")
        self.manager.set_budget("400")
        plan = self.reload().basket_plan()
        self.assertEqual(plan["best_market"], "Dhaka Sadar")
        self.assertEqual(plan["status"][0], "Within budget")

    def test_removing_a_basket_item(self):
        self.manager.set_basket_item("RICE", "2")
        self.manager.remove_basket_item("RICE")
        self.assertEqual(self.manager.basket["items"], {})
        with self.assertRaises(RecordNotFoundError):
            self.manager.remove_basket_item("RICE")

    def test_report_is_saved_as_a_text_file(self):
        path = self.manager.save_report()
        self.assertTrue(Path(path).exists())
        self.assertIn("PRODUCT SUMMARY", Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
