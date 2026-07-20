from pathlib import Path

from src.gui.main_window import MainWindow
from src.gui.splash_screen import SplashScreen

ICON_PATH = Path("assets") / "icons" / "app_icon.ico"


def main() -> None:
    """Application entry point. Shows a splash screen, then the main window."""
    app = MainWindow()
    app.withdraw()  # build the real window hidden, so it never flashes half-built

    if ICON_PATH.exists():
        try:
            app.iconbitmap(str(ICON_PATH))
        except Exception:
            pass

    splash = SplashScreen(app)  # now a proper child of the real root window
    splash.update()

    app.after(900, lambda: _finish_startup(app, splash))
    app.mainloop()


def _finish_startup(app: MainWindow, splash: SplashScreen) -> None:
    """Closes the splash and reveals the fully-built main window."""
    splash.destroy()
    app.deiconify()


if __name__ == "__main__":
    main()