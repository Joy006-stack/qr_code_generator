from pathlib import Path

import customtkinter as ctk

ICON_PATH = Path("assets") / "icons" / "app_icon.ico"

class SplashScreen(ctk.CTkToplevel):
    """
    A brief loading screen shown while the main application window builds.

    This is a CHILD window of the (hidden) MainWindow, which must already
    exist as the Tkinter root before this is created.
    """

    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)

        self.overrideredirect(True)  # no title bar / borders — a clean splash look
        self.geometry("360x220")
        self._center_on_screen()

        self.configure(fg_color="#09090B")

        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except Exception:
                pass  # icon is cosmetic; never let it block startup

        title = ctk.CTkLabel(
            self, text="QR Code Generator",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#F2F2F7",
        )
        title.pack(pady=(60, 10))

        subtitle = ctk.CTkLabel(
            self, text="Loading...", font=ctk.CTkFont(size=13), text_color="#8A8599",
        )
        subtitle.pack()

        progress = ctk.CTkProgressBar(self, width=220, mode="indeterminate")
        progress.pack(pady=30)
        progress.start()

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        width, height = 360, 220
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")