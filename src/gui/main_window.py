from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from src.services.qr_service import (
    ErrorCorrectionLevel,
    OutputFormat,
    QRGenerationError,
    generate_qr_code,
)


class MainWindow(ctk.CTk):
    """
    The main application window for the QR Code Generator.

    This class represents the primary GUI entry point. All top-level
    layout and window configuration lives here.
    """

    ERROR_CORRECTION_OPTIONS = {
        "Low (~7%)": ErrorCorrectionLevel.LOW,
        "Medium (~15%)": ErrorCorrectionLevel.MEDIUM,
        "Quartile (~25%)": ErrorCorrectionLevel.QUARTILE,
        "High (~30%)": ErrorCorrectionLevel.HIGH,
    }

    FORMAT_OPTIONS = {
        "PNG": OutputFormat.PNG,
        "SVG": OutputFormat.SVG,
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("QR Code Generator")
        self.geometry("600x650")
        self.minsize(500, 600)

        # --- Widgets: core input ---
        self.title_label = ctk.CTkLabel(
            self, text="QR Code Generator", font=ctk.CTkFont(size=20, weight="bold")
        )

        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="Enter text or URL", width=350
        )

        # --- Widgets: settings ---
        self.settings_frame = ctk.CTkFrame(self)

        self.error_correction_label = ctk.CTkLabel(
            self.settings_frame, text="Error Correction:"
        )
        self.error_correction_menu = ctk.CTkOptionMenu(
            self.settings_frame, values=list(self.ERROR_CORRECTION_OPTIONS.keys())
        )
        self.error_correction_menu.set("Medium (~15%)")

        self.format_label = ctk.CTkLabel(self.settings_frame, text="Format:")
        self.format_menu = ctk.CTkOptionMenu(
            self.settings_frame, values=list(self.FORMAT_OPTIONS.keys())
        )
        self.format_menu.set("PNG")

        self.box_size_label = ctk.CTkLabel(self.settings_frame, text="Box Size (px):")
        self.box_size_entry = ctk.CTkEntry(self.settings_frame, width=80)
        self.box_size_entry.insert(0, "10")

        self.border_label = ctk.CTkLabel(self.settings_frame, text="Border:")
        self.border_entry = ctk.CTkEntry(self.settings_frame, width=80)
        self.border_entry.insert(0, "4")

        # --- Widgets: action + feedback ---
        self.generate_button = ctk.CTkButton(
            self, text="Generate", command=self.on_generate_click
        )

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")

        # --- Layout: core input ---
        self.title_label.pack(pady=(30, 20))
        self.url_entry.pack(pady=10)

        # --- Layout: settings frame (grid inside this frame) ---
        self.settings_frame.pack(pady=15, padx=20, fill="x")

        self.error_correction_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.error_correction_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.format_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.format_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.box_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.box_size_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.border_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.border_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # --- Layout: action + feedback ---
        self.generate_button.pack(pady=15)
        self.status_label.pack(pady=10)

    def on_generate_click(self) -> None:
        """Handles the Generate button click: reads input/settings, generates a QR code, updates status."""
        entered_text = self.url_entry.get()

        try:
            box_size = int(self.box_size_entry.get())
            border = int(self.border_entry.get())
        except ValueError:
            self.status_label.configure(
                text="Error: Box size and border must be whole numbers.",
                text_color="red",
            )
            return

        error_correction = self.ERROR_CORRECTION_OPTIONS[self.error_correction_menu.get()]
        output_format = self.FORMAT_OPTIONS[self.format_menu.get()]
        output_path = self._build_output_path(output_format)

        try:
            generate_qr_code(
                entered_text,
                output_path,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
                output_format=output_format,
            )
        except QRGenerationError as error:
            self.status_label.configure(text=f"Error: {error}", text_color="red")
            return

        self.status_label.configure(
            text=f"QR code saved to {output_path}", text_color="green"
        )

    def _build_output_path(self, output_format: OutputFormat) -> Path:
        """Builds a unique, timestamped output file path inside the output/ folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = output_format.value
        filename = f"qr_{timestamp}.{extension}"
        return Path("output") / filename