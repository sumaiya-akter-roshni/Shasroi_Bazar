from tkinter import font as tkfont
from tkinter import ttk

BACKGROUND = "#eef2f5"
CARD = "#ffffff"
SOFT = "#f6f9f8"
PRIMARY = "#1f6f5c"
PRIMARY_DARK = "#17574a"
HEADER_NOTE = "#cfe6df"
TEXT = "#1f2933"
MUTED = "#667085"
BORDER = "#d5dbe1"
BUTTON = "#e6ebee"
BUTTON_HOVER = "#d7dfe3"
ROW_ALT = "#f3f7f6"
SELECTED = "#cde9e0"
RED = "#c62828"
ORANGE = "#d97706"
GREEN = "#2e7d32"

LEVEL_COLOURS = {"Spike": RED, "Watch": ORANGE, "Normal": TEXT}
BADGE_COLOURS = {"Spike": RED, "Watch": ORANGE, "Normal": GREEN}
STATUS_COLOURS = {"Within budget": GREEN, "Close to budget": ORANGE,
                  "Over budget": RED, "No budget": MUTED}
BAR_STYLES = {"Within budget": "Green.Horizontal.TProgressbar",
              "Close to budget": "Orange.Horizontal.TProgressbar",
              "Over budget": "Red.Horizontal.TProgressbar",
              "No budget": "Green.Horizontal.TProgressbar"}

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
    points_per_pixel_normal = 96 / 72
    return float(widget.tk.call("tk", "scaling")) / points_per_pixel_normal


def apply_theme(root) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=BACKGROUND)

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

    style.configure("Accent.TButton", background=PRIMARY, foreground="white", font=BOLD,
                    bordercolor=PRIMARY, lightcolor=PRIMARY, darkcolor=PRIMARY,
                    focuscolor=PRIMARY)
    style.map("Accent.TButton", background=[("active", PRIMARY_DARK)],
              lightcolor=[("active", PRIMARY_DARK)], darkcolor=[("active", PRIMARY_DARK)])

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
    for name, colour in (("Green", GREEN), ("Orange", ORANGE), ("Red", RED)):
        style.configure(f"{name}.Horizontal.TProgressbar", background=colour,
                        troughcolor="#e3e8eb", bordercolor="#e3e8eb",
                        lightcolor=colour, darkcolor=colour, thickness=14)
