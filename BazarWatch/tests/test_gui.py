import tkinter as tk
import unittest
from unittest import mock

from manager import BazarManager
from tests.helpers import make_data_folder

try:
    root = tk.Tk()
    root.destroy()
    HAS_SCREEN = True
except tk.TclError:
    HAS_SCREEN = False


@unittest.skipUnless(HAS_SCREEN, "no screen available")
class TestWindow(unittest.TestCase):
    def setUp(self):
        from gui import BazarApp

        self.temp, folder = make_data_folder()
        patcher = mock.patch("gui.messagebox")
        self.messagebox = patcher.start()
        self.addCleanup(patcher.stop)

        self.app = BazarApp(BazarManager(folder, folder / "reports"))
        self.app.withdraw()

    def tearDown(self):
        self.app.destroy()
        self.temp.cleanup()

    def test_the_records_table_shows_the_dataset(self):
        self.assertEqual(len(self.app.records_table.get_children()), 7)

    def test_saving_a_price_shows_its_alert_level(self):
        self.app.add_price.insert(0, "70")
        self.app.add_date.delete(0, "end")
        self.app.add_date.insert(0, "2026-06-15")
        self.app.add_product.set("Rice [RICE]")
        self.app.save_price()
        self.assertIn(self.app.result_label.cget("text"), ("Watch", "Spike"))
        self.assertEqual(len(self.app.records_table.get_children()), 8)

    def test_a_wrong_price_shows_an_error(self):
        self.app.add_price.insert(0, "abc")
        self.app.save_price()
        self.messagebox.showerror.assert_called_once()
        self.assertEqual(self.app.manager.my_records, [])

    def test_summary_cards_follow_the_data(self):
        self.assertEqual(self.app.prices_card.value.cget("text"), "7")
        self.app.add_price.insert(0, "55")
        self.app.save_price()
        self.assertEqual(self.app.prices_card.value.cget("text"), "8")

    def test_the_basket_tab_shows_a_budget_status(self):
        self.app.basket_quantity.delete(0, "end")
        self.app.basket_quantity.insert(0, "2")
        self.app.basket_product.set("Rice [RICE]")
        self.app.add_basket_item()
        self.assertIn("budget", self.app.budget_label.cget("text").lower())


if __name__ == "__main__":
    unittest.main()
