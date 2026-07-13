from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk

from src.services.favicon_service import FavIconFetchError, fetch_favicon, is_valid_http_url
from src.services.qr_service import (
    ErrorCorrectionLevel,
    OutputFormat,
    QRGenerationError,
    generate_qr_code,
)

# Vampire Castle: every color is intentionally dark and muted/desaturated.
# No bright or vivid accents anywhere, including text.
DARK_THEME = {
    "window_bg": "#09090B",       
    "frame_bg": "#13131A",        
    "title_text": "#F2F2F7",      
    "label_text": "#C9C5D4",      

    "entry_bg": "#1A1A24",
    "entry_text": "#F5F5FA",
    "entry_border": "#6E56CF",    

    "button_bg": "#6E56CF",
    "button_hover": "#8467F5",
    "button_text": "#FFFFFF",

    "status_default": "#AFA7C7",
}

LIGHT_THEME = {
    "window_bg": "#FAF7FF",       
    "frame_bg": "#E6DEFF",        
    "title_text": "#2E2548",      
    "label_text": "#43365F",      

    "entry_bg": "#FFFFFF",
    "entry_text": "#2E2548",      
    "entry_border": "#D8C8FF",    

    "button_bg": "#A78BFA",       
    "button_hover": "#8B6FF2",   
    "button_text": "#FFFFFF",

    "status_default": "#5A4F73",  
}

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

    FORMAT_FILE_TYPES = {
        OutputFormat.PNG: [("PNG image", "*.png")],
        OutputFormat.SVG: [("SVG image", "*.svg")],
    }

    LOGO_FILE_TYPES = [
        ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
        ("All files", "*.*"),
    ]

    def __init__(self) -> None:
        super().__init__()

        self.title("QR Code Generator")
        self.geometry("600x880")
        self.minsize(500, 820)

        self.fill_color: str = "#000000"
        self.back_color: str = "#FFFFFF"
        self.logo_path: Path | None = None
        self.current_theme: dict[str, str] = DARK_THEME
        self.is_dark_mode: bool = True

        self.title_label = ctk.CTkLabel(
            self, text="QR Code Generator", font=ctk.CTkFont(size=20, weight="bold")
        )

        # Icon-only toggle: shows the icon of the mode you'd switch TO.
        self.theme_toggle_button = ctk.CTkButton(
            self,
            text="☀️",
            width=44,
            height=32,
            command=self.on_toggle_theme,
        )

        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="Enter text or URL", width=350
        )

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

        self.fill_color_label = ctk.CTkLabel(self.settings_frame, text="QR Color:")
        self.fill_color_button = ctk.CTkButton(
            self.settings_frame,
            text="Choose",
            width=80,
            fg_color=self.fill_color,
            command=self.on_choose_fill_color,
        )

        self.back_color_label = ctk.CTkLabel(self.settings_frame, text="Background Color:")
        self.back_color_button = ctk.CTkButton(
            self.settings_frame,
            text="Choose",
            width=80,
            fg_color=self.back_color,
            text_color="black",
            command=self.on_choose_back_color,
        )

        self.logo_label = ctk.CTkLabel(self.settings_frame, text="Logo:")
        self.logo_button = ctk.CTkButton(
            self.settings_frame,
            text="Choose Logo...",
            width=140,
            command=self.on_choose_logo,
        )
        self.logo_clear_button = ctk.CTkButton(
            self.settings_frame,
            text="Clear",
            width=60,
            fg_color="gray40",
            command=self.on_clear_logo,
        )

        self.auto_favicon_checkbox = ctk.CTkCheckBox(
            self.settings_frame,
            text="Auto-fetch logo from website (if text is a URL)",
            command=self.on_toggle_auto_favicon,
        )

        self.logo_hint_label = ctk.CTkLabel(
            self.settings_frame,
            text="",
            font=ctk.CTkFont(size=11),
            wraplength=400,
            justify="left",
        )

        self.generate_button = ctk.CTkButton(
            self, text="Generate", command=self.on_generate_click
        )

        self.status_label = ctk.CTkLabel(self, text="")

        self.title_label.pack(pady=(25, 5))
        self.theme_toggle_button.pack(pady=(0, 15))
        self.url_entry.pack(pady=10)

        self.settings_frame.pack(pady=15, padx=20, fill="x")

        self.error_correction_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.error_correction_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.format_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.format_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.box_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.box_size_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.border_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.border_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.fill_color_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.fill_color_button.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.back_color_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.back_color_button.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        self.logo_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.logo_button.grid(row=6, column=1, padx=10, pady=10, sticky="w")
        self.logo_clear_button.grid(row=6, column=2, padx=(0, 10), pady=10, sticky="w")

        self.auto_favicon_checkbox.grid(
            row=7, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="w"
        )

        self.logo_hint_label.grid(row=8, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="w")

        self.generate_button.pack(pady=15)
        self.status_label.pack(pady=10)

        self.apply_theme(self.current_theme)

    def apply_theme(self, theme: dict[str, str]) -> None:
        """Applies a color palette dictionary to every themed widget in the window."""
        self.configure(fg_color=theme["window_bg"])
        self.settings_frame.configure(fg_color=theme["frame_bg"])

        self.title_label.configure(text_color=theme["title_text"])

        for label in (
            self.error_correction_label,
            self.format_label,
            self.box_size_label,
            self.border_label,
            self.fill_color_label,
            self.back_color_label,
            self.logo_label,
        ):
            label.configure(text_color=theme["label_text"])

        for entry in (self.url_entry, self.box_size_entry, self.border_entry):
            entry.configure(
                fg_color=theme["entry_bg"],
                text_color=theme["entry_text"],
                border_color=theme["entry_border"],
            )

        for button in (
            self.theme_toggle_button,
            self.logo_button,
            self.generate_button,
        ):
            button.configure(
                fg_color=theme["button_bg"],
                hover_color=theme["button_hover"],
                text_color=theme["button_text"],
            )

        for option_menu in (self.error_correction_menu, self.format_menu):
            option_menu.configure(
                fg_color=theme["button_bg"],
                button_color=theme["button_bg"],
                button_hover_color=theme["button_hover"],
                text_color=theme["button_text"],
            )

        self.auto_favicon_checkbox.configure(text_color=theme["label_text"])
        self.logo_hint_label.configure(text_color=theme["label_text"])
        self.status_label.configure(text_color=theme["status_default"])

    def on_toggle_theme(self) -> None:
        """Switches between the Vampire Castle and Chilled Picnic themes."""
        self.is_dark_mode = not self.is_dark_mode

        if self.is_dark_mode:
            self.current_theme = DARK_THEME
            self.theme_toggle_button.configure(text="☀️")
        else:
            self.current_theme = LIGHT_THEME
            self.theme_toggle_button.configure(text="🌙")

        self.apply_theme(self.current_theme)

    def on_choose_fill_color(self) -> None:
        """Opens a native color picker for the QR pattern (foreground) color."""
        chosen = colorchooser.askcolor(color=self.fill_color, title="Choose QR Color")
        hex_color = chosen[1]
        if hex_color:
            self.fill_color = hex_color
            self.fill_color_button.configure(fg_color=hex_color)

    def on_choose_back_color(self) -> None:
        """Opens a native color picker for the background color."""
        chosen = colorchooser.askcolor(color=self.back_color, title="Choose Background Color")
        hex_color = chosen[1]
        if hex_color:
            self.back_color = hex_color
            self.back_color_button.configure(fg_color=hex_color)

    def on_choose_logo(self) -> None:
        """Opens a file picker for selecting a logo image to embed."""
        self.auto_favicon_checkbox.deselect()

        chosen_path = filedialog.askopenfilename(
            title="Choose Logo Image",
            filetypes=self.LOGO_FILE_TYPES,
        )
        if chosen_path:
            self.logo_path = Path(chosen_path)
            self.logo_hint_label.configure(
                text=f"Selected: {self.logo_path.name} "
                "(error correction will be forced to High)"
            )

    def on_clear_logo(self) -> None:
        """Removes the currently selected logo, if any."""
        self.logo_path = None
        self.auto_favicon_checkbox.deselect()
        self.logo_hint_label.configure(text="")

    def on_toggle_auto_favicon(self) -> None:
        """Handles the auto-fetch-favicon checkbox being toggled on or off."""
        if self.auto_favicon_checkbox.get():
            self.logo_path = None
            self.logo_hint_label.configure(
                text="Will fetch the website's favicon automatically when you click Generate "
                "(error correction will be forced to High)."
            )
        else:
            self.logo_hint_label.configure(text="")

    def on_generate_click(self) -> None:
        """Handles the Generate button click: validates input first, then asks where to save, then generates."""
        entered_text = self.url_entry.get()

        if not entered_text or not entered_text.strip():
            self.status_label.configure(
                text="Error: Please enter some text or a URL before generating.",
                text_color="red",
            )
            return

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

        logo_path_to_use = self.logo_path
        temp_favicon_path: Path | None = None

        if self.auto_favicon_checkbox.get():
            if not is_valid_http_url(entered_text.strip()):
                self.status_label.configure(
                    text="Error: Auto-fetch logo requires the text to be a valid URL.",
                    text_color="red",
                )
                return
            try:
                temp_favicon_path = fetch_favicon(entered_text.strip())
                logo_path_to_use = temp_favicon_path
            except FavIconFetchError as error:
                self.status_label.configure(text=f"Error: {error}", text_color="red")
                return

        if logo_path_to_use is not None and output_format is OutputFormat.SVG:
            self.status_label.configure(
                text="Error: Logo embedding is only supported for PNG, not SVG.",
                text_color="red",
            )
            return

        output_path = self._ask_save_location(output_format)
        if output_path is None:
            return

        try:
            generate_qr_code(
                entered_text,
                output_path,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
                output_format=output_format,
                fill_color=self.fill_color,
                back_color=self.back_color,
                logo_path=logo_path_to_use,
            )
        except QRGenerationError as error:
            self.status_label.configure(text=f"Error: {error}", text_color="red")
            return
        finally:
            if temp_favicon_path is not None:
                temp_favicon_path.unlink(missing_ok=True)

        self.status_label.configure(
            text=f"QR code saved to {output_path}", text_color="green"
        )

    def _ask_save_location(self, output_format: OutputFormat) -> Path | None:
        """
        Opens a native Save As dialog for the user to choose destination and filename.

        Returns:
            The chosen Path, or None if the user cancelled the dialog.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"qr_{timestamp}.{output_format.value}"

        chosen_path = filedialog.asksaveasfilename(
            initialdir="output",
            initialfile=default_filename,
            defaultextension=f".{output_format.value}",
            filetypes=self.FORMAT_FILE_TYPES[output_format],
            title="Save QR Code As",
        )

        if not chosen_path:
            return None

        return Path(chosen_path)