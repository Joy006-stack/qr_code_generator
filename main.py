from src.gui.main_window import MainWindow


def main() -> None:
    """Application entry point. Creates and runs the main window."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()