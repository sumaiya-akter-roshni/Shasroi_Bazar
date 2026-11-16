import ctypes

from gui import BazarApp


def make_text_sharp() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main() -> None:
    make_text_sharp()
    app = BazarApp()
    app.mainloop()


if __name__ == "__main__":
    main()
