"""The Tkinter window of BazarWatch BD.

At the top there is a green header and four summary cards. Below them are
four tabs: Add Price, Records, Statistics and My Basket.

Every button calls the manager. If the manager raises a BazarError
(for example a wrong price), we show its message and the app keeps running.
Colours and fonts come from theme.py.
"""

import tkinter as tk
from datetime import date
from tkinter import messagebox, simpledialog, ttk

# NEW CONTRIBUTION: CSV Export
import csv
from tkinter import filedialog

import config
import theme
from manager import BazarManager
from validators import BazarError

ALL_PRODUCTS = "All products"
WINDOW_WIDTH = 1180   # on a normal screen; bigger on screens with display scaling
WINDOW_HEIGHT = 760
TASKBAR_ROOM = 100    # keep the window above the Windows taskbar
ALERT_MEANINGS = (("Spike", "both rules are true"),
                  ("Watch", "one rule is true"),
                  ("Normal", "no rule is true"))


# ---------- small helpers ----------

def make_table(parent, columns: list, height: int = 10) -> ttk.Treeview:
    """Create a table (Treeview) with a scrollbar.

    columns is a list of (key, heading, width).
    """
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True, pady=(6, 0))

    table = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                         height=height, selectmode="browse")
    factor = theme.screen_factor(parent)
    for key, heading, width in columns:
        table.heading(key, text=heading, anchor="w")
        table.column(key, width=int(width * factor), anchor="w")

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Text colour for each alert level, and a light background on every second row
    for level, colour in theme.LEVEL_COLOURS.items():
        table.tag_configure(level, foreground=colour)
    table.tag_configure("odd", background=theme.ROW_ALT)
    return table


def add_row(table: ttk.Treeview, index: int, values: tuple,
            row_id: str | None = None, level: str = "Normal") -> None:
    """Add one row to a table. Odd rows get a light background (zebra stripes)."""
    stripe = "odd" if index % 2 else "even"
    table.insert("", "end", iid=row_id, values=values, tags=(level, stripe))


def clear_table(table: ttk.Treeview) -> None:
    for row in table.get_children():
        table.delete(row)


def selected_id(table: ttk.Treeview) -> str | None:
    """The ID of the chosen row (we use the record or product ID as the row ID)."""
    selection = table.selection()
    return selection[0] if selection else None


def money(value) -> str:
    return "-" if value is None else f"{value:.2f}"


def soft_panel(parent) -> tk.Frame:
    """A light box with a thin border, used on the right side of some tabs."""
    return tk.Frame(parent, bg=theme.SOFT, highlightthickness=1,
                    highlightbackground=theme.BORDER, padx=20, pady=16)


def panel_title(parent, text: str) -> None:
    tk.Label(parent, text=text.upper(), bg=theme.SOFT, fg=theme.MUTED,
             font=theme.SMALL_BOLD).pack(anchor="w")


def panel_line(parent) -> None:
    tk.Frame(parent, bg=theme.BORDER, height=1).pack(fill="x", pady=14)


class SummaryCard(tk.Frame):
    """A small white box at the top: a title, a big value and a note."""

    def __init__(self, parent, title: str):
        super().__init__(parent, bg=theme.CARD, highlightthickness=1,
                         highlightbackground=theme.BORDER, padx=14, pady=6)
        tk.Label(self, text=title.upper(), bg=theme.CARD, fg=theme.MUTED,
                 font=theme.SMALL_BOLD, anchor="w").pack(fill="x")
        self.value = tk.Label(self, text="-", bg=theme.CARD, fg=theme.TEXT,
                              font=theme.BIG, anchor="w")
        self.value.pack(fill="x")
        self.note = tk.Label(self, text="", bg=theme.CARD, fg=theme.MUTED,
                             font=theme.SMALL, anchor="w")
        self.note.pack(fill="x")

    def show(self, value: str, note: str, colour: str = theme.TEXT) -> None:
        self.value.config(text=value, fg=colour)
        self.note.config(text=note)


class BazarApp(tk.Tk):
    def __init__(self, manager: BazarManager | None = None):
        super().__init__()
        self.manager = manager or BazarManager()
        # {label: product_id}
        self.product_labels = self.manager.product_labels()

        self.title("BazarWatch BD - Food Price Tracker")
        self.fit_to_screen()
        theme.apply_theme(self)

        self.build_header()
        self.build_summary_cards()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.add_tab = ttk.Frame(notebook, padding=16)
        self.records_tab = ttk.Frame(notebook, padding=14)
        self.stats_tab = ttk.Frame(notebook, padding=14)
        self.basket_tab = ttk.Frame(notebook, padding=14)
        notebook.add(self.add_tab, text="Add Price")
        notebook.add(self.records_tab, text="Records")
        notebook.add(self.stats_tab, text="Statistics")
        notebook.add(self.basket_tab, text="My Basket")

        self.build_add_tab()
        self.build_records_tab()
        self.add_extra_record_features()
        self.build_stats_tab()
        self.build_basket_tab()
        self.refresh_all()

        if self.manager.problems:
            messagebox.showwarning(
                "Data problems", "\n".join(self.manager.problems))

    # ---------- helpers ----------

    def fit_to_screen(self) -> None:
        """Open the window at a good size, but never bigger than the screen."""
        factor = theme.screen_factor(self)
        width = min(int(WINDOW_WIDTH * factor), self.winfo_screenwidth() - 40)
        height = min(int(WINDOW_HEIGHT * factor),
                     self.winfo_screenheight() - TASKBAR_ROOM)
        self.geometry(f"{width}x{height}+20+10")
        self.minsize(int(900 * factor), int(560 * factor))

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        """Tkinter calls this if a button causes an error we did not expect.

        We show a message instead of letting the error go unnoticed.
        """
        messagebox.showerror("Unexpected error",
                             f"Something went wrong: {exc_value}\nThe app is still running.")

    def refresh_all(self) -> None:
        """After every change we redraw all tabs and the summary cards."""
        self.refresh_summary()
        self.refresh_records()
        self.refresh_stats()
        self.refresh_basket()

    # ================= Header and summary cards =================

    def build_header(self) -> None:
        header = tk.Frame(self, bg=theme.PRIMARY, padx=20, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="BazarWatch BD", bg=theme.PRIMARY, fg="white",
                 font=theme.HEADER).pack(side="left")
        tk.Label(header, text="Food prices around Dhaka - real WFP prices + your own",
                 bg=theme.PRIMARY, fg=theme.HEADER_NOTE, font=theme.NORMAL).pack(
            side="left", padx=(14, 0), pady=(5, 0))
        tk.Label(header, text=f"Today: {date.today().isoformat()}", bg=theme.PRIMARY,
                 fg=theme.HEADER_NOTE, font=theme.NORMAL).pack(side="right", pady=(5, 0))

    def build_summary_cards(self) -> None:
        row = tk.Frame(self, bg=theme.BACKGROUND, padx=16, pady=10)
        row.pack(fill="x")
        self.prices_card = SummaryCard(row, "Prices saved")
        self.alerts_card = SummaryCard(row, "Unusual prices")
        self.basket_card = SummaryCard(row, "Basket (split plan)")
        self.budget_card = SummaryCard(row, "Weekly budget")

        cards = (self.prices_card, self.alerts_card,
                 self.basket_card, self.budget_card)
        for column, card in enumerate(cards):
            card.grid(row=0, column=column, sticky="nsew",
                      padx=(0 if column == 0 else 12, 0))
            row.columnconfigure(column, weight=1, uniform="cards")

    def refresh_summary(self) -> None:
        manager = self.manager
        dataset, mine = len(manager.dataset_records), len(manager.my_records)
        self.prices_card.show(str(dataset + mine),
                              f"{dataset} from WFP + {mine} yours")

        counts = manager.alert_counts()
        self.alerts_card.show(
            f"{counts['Spike']} Spike",
            f"{counts['Watch']} Watch (last {config.RECENT_DAYS} days)",
            theme.RED if counts["Spike"] else theme.TEXT)

        plan = manager.basket_plan()
        if plan["best_market"]:
            note = f"Best market: {plan['best_market']}"
        else:
            note = "No market has every item"
        self.basket_card.show(f"Tk {plan['split_total']:.2f}", note)

        status = plan["status"][0]
        if status == "No budget":
            self.budget_card.show(
                "-", "Set a weekly budget in My Basket", theme.MUTED)
        else:
            self.budget_card.show(f"{plan['budget_percent']:.0f}% used",
                                  f"{status} (Tk {manager.basket['budget']:g})",
                                  theme.STATUS_COLOURS[status])

    # ================= Tab 1: Add Price =================

    def build_add_tab(self) -> None:
        tab = self.add_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        form = ttk.Frame(tab)
        form.grid(row=0, column=0, sticky="nw")
        ttk.Label(form, text="Add a price you paid", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(form, text="Choose the product and the market, then type the price.",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w",
                                             pady=(2, 16))

        ttk.Label(form, text="Product").grid(
            row=2, column=0, sticky="w", pady=6)
        self.add_product = ttk.Combobox(form, values=list(self.product_labels),
                                        state="readonly", width=34)
        self.add_product.grid(row=2, column=1, sticky="w",
                              padx=(16, 0), pady=6)
        self.add_product.bind("<<ComboboxSelected>>",
                              lambda event: self.show_product_info())

        ttk.Label(form, text="Market").grid(
            row=3, column=0, sticky="w", pady=6)
        self.add_market = ttk.Combobox(
            form, values=config.MARKETS, state="readonly", width=34)
        self.add_market.grid(row=3, column=1, sticky="w", padx=(16, 0), pady=6)

        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=4,
                                                       column=0, sticky="w", pady=6)
        self.add_date = ttk.Entry(form, width=20)
        self.add_date.grid(row=4, column=1, sticky="w", padx=(16, 0), pady=6)

        ttk.Label(form, text="Price per unit (Tk)").grid(
            row=5, column=0, sticky="w", pady=6)
        self.add_price = ttk.Entry(form, width=20)
        self.add_price.grid(row=5, column=1, sticky="w", padx=(16, 0), pady=6)
        self.add_price.bind("<Return>", lambda event: self.save_price())

        self.product_info = ttk.Label(form, text="", style="Muted.TLabel")
        self.product_info.grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(10, 16))

        buttons = ttk.Frame(form)
        buttons.grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Button(buttons, text="Save price", style="Accent.TButton",
                   command=self.save_price).pack(side="left")
        ttk.Button(buttons, text="Clear", command=self.clear_add_form).pack(
            side="left", padx=8)

        self.build_result_panel(tab)
        self.clear_add_form()

    def build_result_panel(self, tab) -> None:
        """The box on the right of the Add Price tab that shows the alert level."""
        panel = soft_panel(tab)
        panel.grid(row=0, column=1, sticky="nsew", padx=(36, 0))

        panel_title(panel, "Result")
        self.result_label = tk.Label(panel, text="", bg=theme.SOFT, fg="white",
                                     font=theme.BADGE, padx=18, pady=4)
        self.result_label.pack(anchor="w", pady=(8, 10))
        self.result_details = tk.Label(panel, text="", bg=theme.SOFT, fg=theme.TEXT,
                                       font=theme.NORMAL, justify="left")
        self.result_details.pack(anchor="w")

        panel_line(panel)
        panel_title(panel, "How the alert works")
        tk.Label(panel, bg=theme.SOFT, fg=theme.TEXT, font=theme.NORMAL, justify="left", text=(
            "Rule 1 - z-score: far above the older prices of this product\n"
            "Rule 2 - reference: far above the official (TCB) price"
        )).pack(anchor="w", pady=(6, 8))
        for level, meaning in ALERT_MEANINGS:
            line = tk.Frame(panel, bg=theme.SOFT)
            line.pack(anchor="w", pady=2)
            tk.Label(line, text=level, width=8, bg=theme.BADGE_COLOURS[level], fg="white",
                     font=theme.SMALL_BOLD).pack(side="left")
            tk.Label(line, text=meaning, bg=theme.SOFT, fg=theme.TEXT,
                     font=theme.NORMAL).pack(side="left", padx=(10, 0))
        tk.Label(panel, bg=theme.SOFT, fg=theme.MUTED, font=theme.SMALL,
                 text="Onion, potato and green chilli change price a lot, "
                      "so they get looser limits.").pack(anchor="w", pady=(10, 0))

    def clear_add_form(self) -> None:
        if self.product_labels:
            self.add_product.current(0)
        self.add_market.current(0)
        self.add_date.delete(0, "end")
        self.add_date.insert(0, date.today().isoformat())
        self.add_price.delete(0, "end")
        self.result_label.config(text="", bg=theme.SOFT)
        self.result_details.config(
            text="Save a price to see if it is normal or too high.")
        self.show_product_info()

    def show_product_info(self) -> None:
        product_id = self.product_labels.get(self.add_product.get())
        if product_id is None:
            return
        product = self.manager.products[product_id]
        reference = product.reference_price
        reference_text = f"Tk {reference:.2f}" if reference else "not set"
        kind = "perishable" if product.is_perishable() else "normal"
        self.product_info.config(text=f"Unit: {product.unit}   |   "
                                 f"Reference price: {reference_text}   |   Type: {kind}")

    def save_price(self) -> None:
        product_id = self.product_labels.get(self.add_product.get())
        try:
            record = self.manager.add_price(product_id, self.add_market.get(),
                                            self.add_date.get(), self.add_price.get())
        except BazarError as error:
            messagebox.showerror("Could not save", str(error))
            return

        self.show_result(record)
        self.add_price.delete(0, "end")
        self.refresh_all()

    def show_result(self, record) -> None:
        """Show the alert level of a saved price, with the numbers behind it."""
        level, z, pct = self.manager.alert_for(record)
        product = self.manager.get_product(record.product_id)
        z_limit, pct_limit = product.spike_limits()

        if z is not None:
            z_text = f"{z:.2f}   (limit {z_limit:g})"
        else:
            z_text = "not enough older prices"
        if pct is not None:
            pct_text = f"{pct:+.1f}%   (limit +{pct_limit:g}%)"
        else:
            pct_text = "reference price not set"

        self.result_label.config(text=level, bg=theme.BADGE_COLOURS[level])
        self.result_details.config(text=(
            f"Saved as {record.record_id}\n"
            f"{product.name}   |   {record.market}   |   {record.date}\n"
            f"Price: Tk {record.price:.2f} per {product.unit}\n\n"
            f"Rule 1 - z-score: {z_text}\n"
            f"Rule 2 - above reference: {pct_text}"))

    # ================= Tab 2: Records =================

    def build_records_tab(self) -> None:
        tab = self.records_tab
        top = ttk.Frame(tab)
        top.pack(fill="x")

        ttk.Label(top, text="Search").pack(side="left")
        self.search_entry = ttk.Entry(top, width=26)
        self.search_entry.pack(side="left", padx=(8, 18))
        self.search_entry.bind(
            "<Return>", lambda event: self.refresh_records())

        ttk.Label(top, text="Product").pack(side="left")
        self.filter_product = ttk.Combobox(
            top, values=[ALL_PRODUCTS, *self.product_labels], state="readonly", width=28)
        self.filter_product.current(0)
        self.filter_product.pack(side="left", padx=(8, 18))
        self.filter_product.bind(
            "<<ComboboxSelected>>", lambda event: self.refresh_records())

        ttk.Button(top, text="Search", style="Accent.TButton",
                   command=self.refresh_records).pack(side="left")
        ttk.Button(top, text="Show all", command=self.show_all_records).pack(
            side="left", padx=8)

        self.records_table = make_table(tab, [
            ("id", "ID", 70), ("product", "Product",
                               160), ("market", "Market", 130),
            ("date", "Date", 90), ("price",
                                   "Price (Tk)", 80), ("source", "Source", 70),
            ("level", "Level", 70), ("z", "z", 60), ("pct", "% vs ref", 80),
        ], height=14)

        bottom = ttk.Frame(tab)
        bottom.pack(fill="x", pady=(10, 0))
        ttk.Button(bottom, text="Edit selected",
                   command=self.edit_record).pack(side="left")
        ttk.Button(bottom, text="Delete selected", style="Danger.TButton",
                   command=self.delete_record).pack(side="left", padx=8)
        self.records_count = ttk.Label(bottom, text="", style="Muted.TLabel")
        self.records_count.pack(side="left", padx=12)
        ttk.Label(bottom, style="Muted.TLabel",
                  text="Only your own prices (source 'mine') can be edited or deleted.").pack(
            side="right")

    def show_all_records(self) -> None:
        self.search_entry.delete(0, "end")
        self.filter_product.current(0)
        self.refresh_records()

    def refresh_records(self) -> None:
        product_id = self.product_labels.get(
            self.filter_product.get())  # None = all
        records = self.manager.search(self.search_entry.get(), product_id)
        alerts = self.manager.all_alerts()

        clear_table(self.records_table)
        for index, record in enumerate(records):
            level, z, pct = alerts[record.record_id]
            add_row(self.records_table, index, row_id=record.record_id, level=level, values=(
                record.record_id,
                self.manager.product_name(record.product_id),
                record.market,
                record.date,
                f"{record.price:.2f}",
                record.source,
                level,
                f"{z:.2f}" if z is not None else "-",
                f"{pct:+.1f}%" if pct is not None else "-",
            ))
        self.records_count.config(text=f"{len(records)} records shown")

    def edit_record(self) -> None:
        record_id = selected_id(self.records_table)
        if record_id is None:
            messagebox.showinfo("Edit", "Please select a record first.")
            return
        record = self.manager.find_record(record_id)
        if not record.can_change():
            messagebox.showinfo("Edit", "Dataset prices cannot be edited. "
                                        "You can only edit your own prices.")
            return
        EditDialog(self, record)

    def delete_record(self) -> None:
        record_id = selected_id(self.records_table)
        if record_id is None:
            messagebox.showinfo("Delete", "Please select a record first.")
            return
        if not messagebox.askyesno("Delete", f"Delete record {record_id}?"):
            return
        try:
            self.manager.delete_price(record_id)
        except BazarError as error:
            messagebox.showerror("Could not delete", str(error))
            return
        self.refresh_all()

    # ================= Tab 3: Statistics =================

    def build_stats_tab(self) -> None:
        tab = self.stats_tab
        top = ttk.Frame(tab)
        top.pack(fill="x")
        ttk.Label(top, text="Statistics per product",
                  style="Section.TLabel").pack(side="left")
        ttk.Label(top, text=f"cheapest market = last {config.RECENT_DAYS} days of data",
                  style="Muted.TLabel").pack(side="left", padx=10)
        ttk.Button(top, text="Save report (.txt)", style="Accent.TButton",
                   command=self.save_report).pack(side="right")
        ttk.Button(top, text="Set reference price",
                   command=self.set_reference_price).pack(side="right", padx=8)

        self.stats_table = make_table(tab, [
            ("product", "Product", 150), ("unit",
                                          "Unit", 50), ("count", "Count", 50),
            ("mean", "Mean", 65), ("median", "Median", 65), ("min", "Min", 60),
            ("max", "Max", 60), ("std", "Std dev",
                                 65), ("reference", "Reference", 75),
            ("cheapest", "Cheapest market", 130), ("cheapest_avg", "Avg there", 75),
        ], height=10)

        ttk.Label(tab, text="Spike and Watch prices (newest first)",
                  style="Section.TLabel").pack(anchor="w", pady=(14, 0))
        self.alerts_table = make_table(tab, [
            ("level", "Level", 70), ("date", "Date",
                                     90), ("product", "Product", 160),
            ("market", "Market", 130), ("price", "Price (Tk)", 80), ("z", "z", 60),
            ("pct", "% vs ref", 80), ("source", "Source", 70),
        ], height=4)

    def refresh_stats(self) -> None:
        clear_table(self.stats_table)
        for index, row in enumerate(self.manager.statistics()):
            product = row["product"]
            market, average = row["cheapest"]
            if row["count"] == 0:
                numbers = ["0", "-", "-", "-", "-", "-"]
            else:
                numbers = [row["count"], money(row["mean"]), money(row["median"]),
                           money(row["min"]), money(row["max"]), money(row["std"])]
            add_row(self.stats_table, index, row_id=product.product_id, values=(
                product.name, product.unit, *
                    numbers, money(product.reference_price),
                    market or "no recent data", money(average),
                    ))

        clear_table(self.alerts_table)
        alerts = self.manager.all_alerts()
        records = sorted(self.manager.all_records(),
                         key=lambda r: r.date, reverse=True)
        unusual = [r for r in records if alerts[r.record_id][0] != "Normal"]
        for index, record in enumerate(unusual):
            level, z, pct = alerts[record.record_id]
            add_row(self.alerts_table, index, row_id=record.record_id, level=level, values=(
                level, record.date, self.manager.product_name(
                    record.product_id),
                record.market, f"{record.price:.2f}",
                f"{z:.2f}" if z is not None else "-",
                f"{pct:+.1f}%" if pct is not None else "-",
                record.source,
            ))

    def set_reference_price(self) -> None:
        product_id = selected_id(self.stats_table)
        if product_id is None:
            messagebox.showinfo("Reference price",
                                "Please select a product first.")
            return
        product = self.manager.products[product_id]
        current = f"{product.reference_price:.2f}" if product.reference_price else ""
        text = simpledialog.askstring(
            "Reference price",
            f"Official (TCB) price of {product.name} per {product.unit}.\n"
            "Leave it empty to remove the reference price.",
            initialvalue=current, parent=self)
        if text is None:  # the user pressed Cancel
            return
        try:
            self.manager.set_reference_price(product_id, text)
        except BazarError as error:
            messagebox.showerror("Could not save", str(error))
            return
        self.refresh_all()
        self.show_product_info()

    def save_report(self) -> None:
        try:
            path = self.manager.save_report()
        except BazarError as error:
            messagebox.showerror("Could not save", str(error))
            return
        messagebox.showinfo(
            "Report saved", f"The report was saved to:\n{path}")

    # ================= Tab 4: My Basket =================

    def build_basket_tab(self) -> None:
        tab = self.basket_tab
        tab.columnconfigure(0, weight=3)
        tab.columnconfigure(1, weight=2)
        tab.rowconfigure(1, weight=1)

        form = ttk.Frame(tab)
        form.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(form, text="Product").pack(side="left")
        self.basket_product = ttk.Combobox(form, values=list(self.product_labels),
                                           state="readonly", width=30)
        if self.product_labels:
            self.basket_product.current(0)
        self.basket_product.pack(side="left", padx=(8, 18))

        ttk.Label(form, text="Quantity").pack(side="left")
        self.basket_quantity = ttk.Entry(form, width=8)
        self.basket_quantity.insert(0, "1")
        self.basket_quantity.pack(side="left", padx=(8, 18))
        ttk.Button(form, text="Add / update item", style="Accent.TButton",
                   command=self.add_basket_item).pack(side="left")
        ttk.Button(form, text="Remove selected", command=self.remove_basket_item).pack(
            side="left", padx=8)

        tables = ttk.Frame(tab)
        tables.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        ttk.Label(tables, text="Items (each at its cheapest market)",
                  style="Section.TLabel").pack(anchor="w")
        self.basket_table = make_table(tables, [
            ("product", "Product", 160), ("quantity", "Quantity", 70),
            ("market", "Cheapest market", 140), ("price",
                                                 "Price", 70), ("cost", "Cost", 80),
        ], height=6)
        ttk.Label(tables, text="Whole basket from one market",
                  style="Section.TLabel").pack(anchor="w", pady=(14, 0))
        self.totals_table = make_table(tables, [
            ("market", "Market", 170), ("total", "Total (Tk)", 100),
        ], height=4)

        self.build_budget_panel(tab)

    def build_budget_panel(self, tab) -> None:
        """The box on the right of the basket tab: the plan and the budget."""
        panel = soft_panel(tab)
        panel.grid(row=1, column=1, sticky="nsew", padx=(20, 0), pady=(14, 0))

        # long lines go onto the next line
        wrap = int(360 * theme.screen_factor(self))
        panel_title(panel, "Your plan")
        self.basket_summary = tk.Label(panel, text="", bg=theme.SOFT, fg=theme.TEXT,
                                       font=theme.NORMAL, justify="left", wraplength=wrap)
        self.basket_summary.pack(anchor="w", pady=(6, 0))

        panel_line(panel)
        panel_title(panel, "Weekly budget")
        budget_row = tk.Frame(panel, bg=theme.SOFT)
        budget_row.pack(anchor="w", pady=(8, 12))
        tk.Label(budget_row, text="Tk", bg=theme.SOFT, fg=theme.TEXT,
                 font=theme.NORMAL).pack(side="left")
        self.budget_entry = ttk.Entry(budget_row, width=12)
        self.budget_entry.pack(side="left", padx=8)
        ttk.Button(budget_row, text="Save budget",
                   command=self.save_budget).pack(side="left")

        self.budget_bar = ttk.Progressbar(panel, maximum=100,
                                          style=theme.BAR_STYLES["Within budget"])
        self.budget_bar.pack(fill="x")
        self.budget_label = tk.Label(panel, text="", bg=theme.SOFT, font=theme.BOLD,
                                     justify="left", wraplength=wrap)
        self.budget_label.pack(anchor="w", pady=(8, 0))

    def refresh_basket(self) -> None:
        basket = self.manager.basket
        self.budget_entry.delete(0, "end")
        self.budget_entry.insert(0, f"{basket['budget']:g}")

        plan = self.manager.basket_plan()

        clear_table(self.basket_table)
        for index, (product_id, quantity) in enumerate(basket["items"].items()):
            name = self.manager.product_name(product_id)
            if product_id in plan["split_plan"]:
                market, price, cost = plan["split_plan"][product_id]
                values = (name, f"{quantity:g}", market,
                          money(price), money(cost))
            else:
                values = (name, f"{quantity:g}", "no recent price", "-", "-")
            add_row(self.basket_table, index, values, row_id=product_id)

        clear_table(self.totals_table)
        totals = sorted(plan["totals"].items(),
                        key=lambda item: item[1])  # cheapest first
        for index, (market, total) in enumerate(totals):
            add_row(self.totals_table, index, (market, money(total)))

        lines = [f"Split plan: Tk {plan['split_total']:.2f}",
                 "(each item at its cheapest market)", ""]
        if plan["best_market"]:
            lines.append(f"Best single market: {plan['best_market']}")
            lines.append(f"Whole basket there: Tk {plan['best_total']:.2f}")
            lines.append("")
            lines.append(f"You save by splitting: Tk {plan['saving']:.2f}")
        else:
            lines.append("No single market has a recent price for every item.")
        if plan["unpriced"]:
            names = ", ".join(self.manager.product_name(pid)
                              for pid in plan["unpriced"])
            lines.append(
                f"No recent price for: {names} (left out of the totals)")
        self.basket_summary.config(text="\n".join(lines))

        status, message = plan["status"]
        self.budget_bar.config(value=min(plan["budget_percent"], 100),
                               style=theme.BAR_STYLES[status])
        self.budget_label.config(
            text=f"{status}\n{message}", fg=theme.STATUS_COLOURS[status])

    def add_basket_item(self) -> None:
        product_id = self.product_labels.get(self.basket_product.get())
        try:
            self.manager.set_basket_item(
                product_id, self.basket_quantity.get())
        except BazarError as error:
            messagebox.showerror("Could not add", str(error))
            return
        self.refresh_all()

    def remove_basket_item(self) -> None:
        product_id = selected_id(self.basket_table)
        if product_id is None:
            messagebox.showinfo(
                "Remove", "Please select an item in the table first.")
            return
        try:
            self.manager.remove_basket_item(product_id)
        except BazarError as error:
            messagebox.showerror("Could not remove", str(error))
            return
        self.refresh_all()

    def save_budget(self) -> None:
        try:
            self.manager.set_budget(self.budget_entry.get())
        except BazarError as error:
            messagebox.showerror("Could not save", str(error))
            return
        self.refresh_all()

    # ==========================================
    # NEW CONTRIBUTIONS
    # Market Filter, Alert Filter, CSV Export
    # ==========================================

    def add_extra_record_features(self):
        """Add extra record filtering and export features."""

        filter_bar = ttk.Frame(self.records_tab)

        # Place the new filter row before the existing records table
        filter_bar.pack(
            fill="x",
            pady=(8, 4),
            before=self.records_table.master
        )

        # Market Filter
        ttk.Label(filter_bar, text="Market:").pack(side="left")

        self.extra_market_filter = ttk.Combobox(
            filter_bar,
            values=["All Markets", *config.MARKETS],
            state="readonly",
            width=17
        )

        self.extra_market_filter.current(0)
        self.extra_market_filter.pack(side="left", padx=6)

        # Alert Filter
        ttk.Label(filter_bar, text="Alert:").pack(
            side="left", padx=(10, 0)
        )

        self.extra_alert_filter = ttk.Combobox(
            filter_bar,
            values=["All Levels", *config.ALERT_LEVELS],
            state="readonly",
            width=13
        )

        self.extra_alert_filter.current(0)
        self.extra_alert_filter.pack(side="left", padx=6)

        # Apply Filters Button
        ttk.Button(
            filter_bar,
            text="Apply Filters",
            command=self.apply_extra_record_filters
        ).pack(side="left", padx=5)

        # Reset Filters Button
        ttk.Button(
            filter_bar,
            text="Reset Filters",
            command=self.reset_extra_record_filters
        ).pack(side="left", padx=5)

        # Export CSV Button
        ttk.Button(
            filter_bar,
            text="Export CSV",
            style="Accent.TButton",
            command=self.export_visible_records_csv
        ).pack(side="right", padx=5)

        # Apply filters when dropdown selections change
        self.extra_market_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_extra_record_filters()
        )

        self.extra_alert_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_extra_record_filters()
        )

        # Apply extra filters after the original search events
        self.filter_product.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_extra_record_filters(),
            add="+"
        )

        self.search_entry.bind(
            "<Return>",
            lambda event: self.apply_extra_record_filters(),
            add="+"
        )

    def apply_extra_record_filters(self):
        """Filter records using market and alert level."""

        # Keep original record loading logic
        self.refresh_records()

        selected_market = self.extra_market_filter.get()
        selected_level = self.extra_alert_filter.get()

        for record_id in self.records_table.get_children():

            values = self.records_table.item(
                record_id, "values"
            )

            record_market = values[2]
            record_level = values[6]

            market_match = (
                selected_market == "All Markets"
                or record_market == selected_market
            )

            level_match = (
                selected_level == "All Levels"
                or record_level == selected_level
            )

            if not (market_match and level_match):
                self.records_table.delete(record_id)

        self.records_count.config(
            text=f"{len(self.records_table.get_children())} records shown"
        )

    def reset_extra_record_filters(self):
        """Reset additional filters."""

        self.extra_market_filter.current(0)
        self.extra_alert_filter.current(0)

        # Use original Show All functionality
        self.show_all_records()

    def export_visible_records_csv(self):
        """Export currently visible records to CSV."""

        visible_records = self.records_table.get_children()

        if not visible_records:
            messagebox.showinfo(
                "Export CSV",
                "No records available to export."
            )
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Records",
            defaultextension=".csv",
            initialfile="bazarwatch_records.csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as csv_file:

                writer = csv.writer(csv_file)

                # Write column headings
                writer.writerow([
                    self.records_table.heading(
                        column, "text"
                    )
                    for column in self.records_table["columns"]
                ])

                # Write visible records
                for record_id in visible_records:

                    values = self.records_table.item(
                        record_id, "values"
                    )

                    writer.writerow(values)

            messagebox.showinfo(
                "Export Successful",
                f"Records exported successfully!\n{file_path}"
            )

        except (OSError, csv.Error) as error:

            messagebox.showerror(
                "Export Failed",
                str(error)
            )


class EditDialog(tk.Toplevel):
    """A small window to change the market, date or price of one of your prices."""

    def __init__(self, app: BazarApp, record):
        super().__init__(app)
        self.app = app
        self.record = record
        self.title(f"Edit {record.record_id}")
        self.configure(background=theme.CARD)
        self.resizable(False, False)
        self.transient(app)

        frame = ttk.Frame(self, padding=18)
        frame.pack()
        ttk.Label(frame, text=f"Edit {app.manager.product_name(record.product_id)}",
                  style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w",
                                               pady=(0, 10))

        ttk.Label(frame, text="Market").grid(
            row=1, column=0, sticky="w", pady=5)
        self.market = ttk.Combobox(
            frame, values=config.MARKETS, state="readonly", width=22)
        self.market.set(record.market)
        self.market.grid(row=1, column=1, padx=(12, 0), pady=5)

        ttk.Label(frame, text="Date").grid(row=2, column=0, sticky="w", pady=5)
        self.date = ttk.Entry(frame, width=25)
        self.date.insert(0, record.date)
        self.date.grid(row=2, column=1, padx=(12, 0), pady=5)

        ttk.Label(frame, text="Price (Tk)").grid(
            row=3, column=0, sticky="w", pady=5)
        self.price = ttk.Entry(frame, width=25)
        self.price.insert(0, f"{record.price:g}")
        self.price.grid(row=3, column=1, padx=(12, 0), pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel",
                   command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", style="Accent.TButton",
                   command=self.save).pack(side="right", padx=8)

        self.grab_set()  # the main window waits until this one is closed

    def save(self) -> None:
        try:
            self.app.manager.update_price(self.record.record_id, self.market.get(),
                                          self.date.get(), self.price.get())
        except BazarError as error:
            # Keep the window open so the user can fix the value
            messagebox.showerror("Could not save", str(error), parent=self)
            return
        self.destroy()
        self.app.refresh_all()
