"""How the app looks: colours, fonts and ttk styles.

gui.py decides WHAT is shown. This file decides HOW it looks, so the
colours can be changed in one place.
"""

from tkinter import font as tkfont
from tkinter import ttk

# ---------- colours ----------
BACKGROUND = "#eef2f5"   # behind the cards and the tabs
CARD = "#ffffff"         # tabs, tables and cards
SOFT = "#f6f9f8"         # side panels (result box, budget box)
PRIMARY = "#1f6f5c"      # header and main buttons
PRIMARY_DARK = "#17574a"
HEADER_NOTE = "#cfe6df"  # small text on the green header
TEXT = "#1f2933"
MUTED = "#667085"
BORDER = "#d5dbe1"
BUTTON = "#e6ebee"
BUTTON_HOVER = "#d7dfe3"
ROW_ALT = "#f3f7f6"      # every second table row
SELECTED = "#cde9e0"
RED = "#c62828"
ORANGE = "#d97706"
GREEN = "#2e7d32"

# Text colour of a table row for each alert level
LEVEL_COLOURS = {"Spike": RED, "Watch": ORANGE, "Normal": TEXT}
# Background of the big level badge in the Add Price tab
BADGE_COLOURS = {"Spike": RED, "Watch": ORANGE, "Normal": GREEN}
STATUS_COLOURS = {"Within budget": GREEN, "Close to budget": ORANGE,
                  "Over budget": RED, "No budget": MUTED}
BAR_STYLES = {"Within budget": "Green.Horizontal.TProgressbar",
              "Close to budget": "Orange.Horizontal.TProgressbar",
              "Over budget": "Red.Horizontal.TProgressbar",
              "No budget": "Green.Horizontal.TProgressbar"}

# ---------- fonts ----------
FONT = "Segoe UI"
NORMAL = (FONT, 10)
BOLD = (FONT, 10, "bold")
SMALL = (FONT, 9)
SMALL_BOLD = (FONT, 8, "bold")
SECTION = (FONT, 11, "bold")
TITLE = (FONT, 14, "bold")
BIG = (FONT, 15, "bold")
BADGE = (FONT, 15, "bold")
HEADER = (FONT, 16, "bold")


def screen_factor(widget) -> float:
    """1.0 on a normal screen, about 1.5 on a screen with 150% display scaling.

    Fonts grow by themselves on such screens, so we use this number to make
    sizes in pixels (window size, table columns) grow too.
    """
    points_per_pixel_normal = 96 / 72
    return float(widget.tk.call("tk", "scaling")) / points_per_pixel_normal


def apply_theme(root) -> None:
    """Set the colours and fonts of every ttk widget in the window."""
    style = ttk.Style(root)
    style.theme_use("clam")  # "clam" lets us change colours on every computer
    root.configure(background=BACKGROUND)

    # Default for all ttk widgets
    style.configure(".", background=CARD, foreground=TEXT, font=NORMAL,
                    bordercolor=BORDER, lightcolor=CARD, darkcolor=CARD)

    style.configure("TLabel", background=CARD, foreground=TEXT)
    style.configure("Title.TLabel", font=TITLE)
    style.configure("Section.TLabel", font=SECTION, foreground=PRIMARY)
    style.configure("Muted.TLabel", foreground=MUTED)

    style_buttons(style)
    style_inputs(style, root)
    style_tabs_and_tables(style, root)
    style_budget_bars(style)


def style_buttons(style: ttk.Style) -> None:
    style.configure("TButton", background=BUTTON, foreground=TEXT, padding=(14, 6),
                    bordercolor=BUTTON, lightcolor=BUTTON, darkcolor=BUTTON, focuscolor=BUTTON)
    style.map("TButton", background=[("active", BUTTON_HOVER)],
              lightcolor=[("active", BUTTON_HOVER)], darkcolor=[("active", BUTTON_HOVER)])

    # Green button for the main action of each tab
    style.configure("Accent.TButton", background=PRIMARY, foreground="white", font=BOLD,
                    bordercolor=PRIMARY, lightcolor=PRIMARY, darkcolor=PRIMARY,
                    focuscolor=PRIMARY)
    style.map("Accent.TButton", background=[("active", PRIMARY_DARK)],
              lightcolor=[("active", PRIMARY_DARK)], darkcolor=[("active", PRIMARY_DARK)])

    # Red text for delete
    style.configure("Danger.TButton", foreground=RED)


def style_inputs(style: ttk.Style, root) -> None:
    style.configure("TEntry", fieldbackground="white", padding=5,
                    lightcolor=BORDER, darkcolor=BORDER)
    style.map("TEntry", bordercolor=[("focus", PRIMARY)], lightcolor=[("focus", PRIMARY)])

    style.configure("TCombobox", fieldbackground="white", background=BUTTON, padding=4,
                    arrowcolor=TEXT, lightcolor=BORDER, darkcolor=BORDER)
    style.map("TCombobox",
              fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")],
              selectforeground=[("readonly", TEXT)],
              bordercolor=[("focus", PRIMARY)])
    # The list that drops down from a combobox is a plain Tk widget
    root.option_add("*TCombobox*Listbox.font", NORMAL)
    root.option_add("*TCombobox*Listbox.selectBackground", PRIMARY)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")


def style_tabs_and_tables(style: ttk.Style, root) -> None:
    style.configure("TNotebook", background=BACKGROUND, borderwidth=0,
                    lightcolor=BACKGROUND, darkcolor=BACKGROUND)
    style.configure("TNotebook.Tab", background=BUTTON, foreground=MUTED, padding=(16, 6),
                    font=BOLD, lightcolor=BUTTON, bordercolor=BORDER)
    style.map("TNotebook.Tab",
              background=[("selected", CARD)],
              foreground=[("selected", PRIMARY)],
              lightcolor=[("selected", CARD)])

    # Row height = height of one line of text + a little space,
    # so the rows also look right on screens with display scaling
    line_height = tkfont.Font(root=root, font=NORMAL).metrics("linespace")
    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=line_height + 7, bordercolor=BORDER)
    style.map("Treeview", background=[("selected", SELECTED)],
              foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background="#e3ebe8", foreground=TEXT, font=BOLD,
                    padding=(6, 5), bordercolor=BORDER, lightcolor="#e3ebe8",
                    darkcolor=BORDER)
    style.map("Treeview.Heading", background=[("active", "#d4e2dc")])

    style.configure("Vertical.TScrollbar", background=BUTTON, troughcolor=CARD,
                    bordercolor=CARD, arrowcolor=MUTED, lightcolor=BUTTON, darkcolor=BUTTON)


def style_budget_bars(style: ttk.Style) -> None:
    """One progress bar style per colour: green, orange and red."""
    for name, colour in (("Green", GREEN), ("Orange", ORANGE), ("Red", RED)):
        style.configure(f"{name}.Horizontal.TProgressbar", background=colour,
                        troughcolor="#e3e8eb", bordercolor="#e3e8eb",
                        lightcolor=colour, darkcolor=colour, thickness=14)
