"""BazarWatch BD - start the app with:  python main.py"""

import ctypes

from gui import BazarApp


def make_text_sharp() -> None:
    """Ask Windows to draw the window sharp on screens with display scaling.

    Without this, Windows stretches the window on a 125% or 150% screen and
    the text looks blurry. On other systems there is no ctypes.windll, so we
    simply skip it - the app works the same, only the text is less sharp.
    """
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
