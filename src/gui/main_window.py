from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from src.services.qr_service import QRGenerationError, generate_qr_code


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
        """Handles the Generate button click: reads input, generates a QR code, updates status."""
        entered_text = self.url_entry.get()
        output_path = self._build_output_path()

        try:
            generate_qr_code(entered_text, output_path)
        except QRGenerationError as error:
            self.status_label.configure(text=f"Error: {error}", text_color="red")
            return

        self.status_label.configure(
            text=f"QR code saved to {output_path}", text_color="green"
        )

    def _build_output_path(self) -> Path:
        """Builds a unique, timestamped output file path inside the output/ folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qr_{timestamp}.png"
        return Path("output") / filename