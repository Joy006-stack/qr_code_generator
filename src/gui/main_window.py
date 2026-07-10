import customtkinter as ctk


class MainWindow(ctk.CTk):
    """
    The main application window for the QR Code Generator.

    This class represents the primary GUI entry point. All top-level
    layout and window configuration lives here.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("QR Code Generator")
        self.geometry("600x500")
        self.minsize(500, 400)

        # --- Widgets ---
        self.title_label = ctk.CTkLabel(
            self, text="QR Code Generator", font=ctk.CTkFont(size=20, weight="bold")
        )

        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="Enter text or URL", width=350
        )

        self.generate_button = ctk.CTkButton(
            self, text="Generate", command=self.on_generate_click
        )

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")

        # --- Layout ---
        self.title_label.pack(pady=(30, 20))
        self.url_entry.pack(pady=10)
        self.generate_button.pack(pady=10)
        self.status_label.pack(pady=10)

    def on_generate_click(self) -> None:
        """Placeholder handler for the Generate button. Real QR logic comes in Phase 5."""
        entered_text = self.url_entry.get()
        print(f"Generate clicked. Entry contains: '{entered_text}'")
        self.status_label.configure(text="Button click registered (no QR logic yet).")