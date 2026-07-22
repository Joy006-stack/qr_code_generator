from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog
import tempfile

import customtkinter as ctk
from PIL import Image

from src.services.favicon_service import FavIconFetchError, fetch_favicon, is_valid_http_url
from src.services.qr_service import (
    ErrorCorrectionLevel,
    OutputFormat,
    QRGenerationError,
    generate_qr_code,
)
from src.gui.tooltip import Tooltip

DARK_THEME = {
    "window_bg": "#09090B",
    "card_bg": "#15151E",
    "accent": "#6E56CF",
    "accent_hover": "#8467F5",
    "ink": "#F2F2F7",
    "muted": "#8A8599",
    "entry_bg": "#1A1A24",
    "entry_text": "#F5F5FA",
    "entry_border": "#332B4D",
    "button_text": "#FFFFFF",
    "status_default": "#AFA7C7",
}

LIGHT_THEME = {
    "window_bg": "#FAF7FF",
    "card_bg": "#FFFFFF",
    "accent": "#7C5CFC",
    "accent_hover": "#6A4AE0",
    "ink": "#2E2548",
    "muted": "#8377A0",
    "entry_bg": "#F6F1FF",
    "entry_text": "#2E2548",
    "entry_border": "#E0D6FF",
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

    SPACE_XS = 8
    SPACE_SM = 16
    SPACE_MD = 24
    SPACE_LG = 32

    PREVIEW_SIZE = 200
    CONTENT_WIDTH = 640
    DEBOUNCE_MS = 300

    def __init__(self) -> None:
        super().__init__()

        self.title("QR Code Generator")
        self.geometry("760x820")
        self.minsize(500, 500)

        self.fill_color: str = "#000000"
        self.back_color: str = "#FFFFFF"
        self.logo_path: Path | None = None
        self.current_theme: dict[str, str] = DARK_THEME
        self.is_dark_mode: bool = True

        self._pending_preview_path: Path | None = None
        self._pending_logo_for_save: Path | None = None
        self._pending_favicon_temp_path: Path | None = None
        self._pending_params: dict | None = None

        blank = Image.new("RGBA", (self.PREVIEW_SIZE, self.PREVIEW_SIZE), (0, 0, 0, 0))
        self._blank_preview_image = ctk.CTkImage(
            light_image=blank, dark_image=blank, size=(self.PREVIEW_SIZE, self.PREVIEW_SIZE)
        )
        self._current_preview_image: ctk.CTkImage = self._blank_preview_image

        self._debounce_after_id: str | None = None

        self._card_content_frames: list[ctk.CTkFrame] = []
        self._eyebrow_labels: list[ctk.CTkLabel] = []

        self._build_header()
        self._build_scroll_area()
        self._build_content_card()
        self._build_style_card()
        self._build_logo_card()
        self._build_preview_card()
        self._build_footer()

        self._bind_shortcuts()

        self.apply_theme(self.current_theme)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        """
        Global keyboard shortcuts, bound to the window itself so they work
        regardless of which widget currently has focus.
        """
        self.bind("<Control-n>", lambda event: self.on_clear_click())
        self.bind("<Control-N>", lambda event: self.on_clear_click())
        self.bind("<Control-s>", lambda event: self.on_save_click())
        self.bind("<Control-S>", lambda event: self.on_save_click())
        self.bind("<Control-g>", lambda event: self._generate_preview())
        self.bind("<Control-G>", lambda event: self._generate_preview())

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=self.SPACE_MD, pady=(self.SPACE_MD, self.SPACE_SM))

        self.title_label = ctk.CTkLabel(
            self.header_frame, text="QR Code Generator",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=28, weight="bold"),
        )
        self.title_label.pack(side="left")

        self.theme_toggle_button = ctk.CTkButton(
            self.header_frame, text="☀️", width=42, height=34, corner_radius=10,
            command=self.on_toggle_theme,
        )
        self.theme_toggle_button.pack(side="right")
        Tooltip(self.theme_toggle_button, "Switch theme")

    def _build_scroll_area(self) -> None:
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.content_column = ctk.CTkFrame(
            self.scroll_frame, fg_color="transparent", width=self.CONTENT_WIDTH
        )
        self.content_column.grid(row=0, column=0, pady=(0, self.SPACE_MD))
        self.content_column.grid_propagate(False)
        self.content_column.configure(width=self.CONTENT_WIDTH)

    def _make_card(self, eyebrow_text: str) -> ctk.CTkFrame:
        content_frame = ctk.CTkFrame(self.content_column, corner_radius=14)
        content_frame.pack(fill="x", pady=(0, self.SPACE_SM))

        eyebrow = ctk.CTkLabel(
            content_frame,
            text=" ".join(list(eyebrow_text.upper())),
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        )
        eyebrow.pack(fill="x", padx=self.SPACE_SM, pady=(self.SPACE_SM, self.SPACE_XS))

        self._card_content_frames.append(content_frame)
        self._eyebrow_labels.append(eyebrow)

        return content_frame

    def _build_content_card(self) -> None:
        card = self._make_card("Content")

        entry_row = ctk.CTkFrame(card, fg_color="transparent")
        entry_row.pack(fill="x", padx=self.SPACE_SM, pady=(0, self.SPACE_SM))
        entry_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            entry_row, placeholder_text="Enter text or URL", height=42,
            corner_radius=10, font=ctk.CTkFont(size=14),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, self.SPACE_XS))
        self.url_entry.bind("<Return>", lambda event: self._schedule_auto_preview())
        self.url_entry.bind("<FocusOut>", lambda event: self._schedule_auto_preview())

        self.clear_button = ctk.CTkButton(
            entry_row, text="Clear", width=70, height=42, corner_radius=10,
            command=self.on_clear_click,
        )
        self.clear_button.grid(row=0, column=1)
        Tooltip(self.clear_button, "Clear everything (Ctrl+N)")

    def _build_style_card(self) -> None:
        card = self._make_card("Style")

        grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=self.SPACE_SM, pady=(0, self.SPACE_SM))
        grid_frame.grid_columnconfigure(1, weight=1)

        self.error_correction_label = ctk.CTkLabel(grid_frame, text="Error Correction", anchor="w")
        self.error_correction_menu = ctk.CTkOptionMenu(
            grid_frame, values=list(self.ERROR_CORRECTION_OPTIONS.keys()), corner_radius=8,
            command=lambda choice: self._schedule_auto_preview(),
        )
        self.error_correction_menu.set("Medium (~15%)")
        Tooltip(self.error_correction_menu, "How much damage the QR code can tolerate and still scan")

        self.format_label = ctk.CTkLabel(grid_frame, text="Format", anchor="w")
        self.format_menu = ctk.CTkOptionMenu(
            grid_frame, values=list(self.FORMAT_OPTIONS.keys()), corner_radius=8,
            command=lambda choice: self._schedule_auto_preview(),
        )
        self.format_menu.set("PNG")
        Tooltip(self.format_menu, "PNG (image) or SVG (scalable vector)")

        self.box_size_label = ctk.CTkLabel(grid_frame, text="Box Size (px)", anchor="w")
        self.box_size_entry = ctk.CTkEntry(grid_frame, width=90, corner_radius=8)
        self.box_size_entry.insert(0, "10")
        self.box_size_entry.bind("<Return>", lambda event: self._schedule_auto_preview())
        self.box_size_entry.bind("<FocusOut>", lambda event: self._schedule_auto_preview())

        self.border_label = ctk.CTkLabel(grid_frame, text="Border", anchor="w")
        self.border_entry = ctk.CTkEntry(grid_frame, width=90, corner_radius=8)
        self.border_entry.insert(0, "4")
        self.border_entry.bind("<Return>", lambda event: self._schedule_auto_preview())
        self.border_entry.bind("<FocusOut>", lambda event: self._schedule_auto_preview())

        self.fill_color_label = ctk.CTkLabel(grid_frame, text="QR Color", anchor="w")
        self.fill_color_button = ctk.CTkButton(
            grid_frame, text="", width=44, height=28, corner_radius=8,
            fg_color=self.fill_color, command=self.on_choose_fill_color,
        )
        Tooltip(self.fill_color_button, "Choose the QR pattern color")

        self.back_color_label = ctk.CTkLabel(grid_frame, text="Background Color", anchor="w")
        self.back_color_button = ctk.CTkButton(
            grid_frame, text="", width=44, height=28, corner_radius=8,
            fg_color=self.back_color, border_width=1, command=self.on_choose_back_color,
        )
        Tooltip(self.back_color_button, "Choose the background color")

        rows = [
            (self.error_correction_label, self.error_correction_menu),
            (self.format_label, self.format_menu),
            (self.box_size_label, self.box_size_entry),
            (self.border_label, self.border_entry),
            (self.fill_color_label, self.fill_color_button),
            (self.back_color_label, self.back_color_button),
        ]
        for row_index, (label, control) in enumerate(rows):
            label.grid(row=row_index, column=0, padx=(0, self.SPACE_XS),
                       pady=self.SPACE_XS, sticky="w")
            control.grid(row=row_index, column=1, padx=(0, self.SPACE_SM),
                         pady=self.SPACE_XS, sticky="w")

    def _build_logo_card(self) -> None:
        card = self._make_card("Logo")

        row_frame = ctk.CTkFrame(card, fg_color="transparent")
        row_frame.pack(fill="x", padx=self.SPACE_SM, pady=(0, self.SPACE_XS))

        self.logo_button = ctk.CTkButton(
            row_frame, text="Choose Logo...", width=150, corner_radius=8,
            command=self.on_choose_logo,
        )
        self.logo_button.pack(side="left")
        Tooltip(self.logo_button, "Pick an image to embed in the center of the QR code")

        self.logo_clear_button = ctk.CTkButton(
            row_frame, text="Clear Logo", width=90, corner_radius=8,
            command=self.on_clear_logo,
        )
        self.logo_clear_button.pack(side="left", padx=(self.SPACE_XS, 0))
        Tooltip(self.logo_clear_button, "Remove the selected logo")

        self.auto_favicon_checkbox = ctk.CTkCheckBox(
            card, text="Auto-fetch logo from website (if text is a URL)",
            command=self.on_toggle_auto_favicon,
        )
        self.auto_favicon_checkbox.pack(fill="x", padx=self.SPACE_SM, pady=(self.SPACE_XS, self.SPACE_XS))
        Tooltip(self.auto_favicon_checkbox, "Automatically use the website's own icon as the logo")

        self.logo_hint_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=11), wraplength=self.CONTENT_WIDTH - 60,
            justify="left", anchor="w",
        )
        self.logo_hint_label.pack(fill="x", padx=self.SPACE_SM, pady=(0, self.SPACE_SM))

    def _build_preview_card(self) -> None:
        card = self._make_card("Preview")

        self.preview_image_label = ctk.CTkLabel(
            card, text="Type something and press Enter, or change a setting, to see a preview.",
            height=self.PREVIEW_SIZE, font=ctk.CTkFont(size=12),
        )
        self.preview_image_label.pack(padx=self.SPACE_SM, pady=(0, self.SPACE_SM))

    def _build_footer(self) -> None:
        self.save_button = ctk.CTkButton(
            self.content_column, text="Save As...", height=46, corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"), state="disabled",
            command=self.on_save_click,
        )
        self.save_button.pack(fill="x", pady=(0, self.SPACE_XS))
        Tooltip(self.save_button, "Save the previewed QR code to a file (Ctrl+S)")

        self.status_label = ctk.CTkLabel(self.content_column, text="")
        self.status_label.pack(pady=(0, self.SPACE_SM))

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def apply_theme(self, theme: dict[str, str]) -> None:
        self.configure(fg_color=theme["window_bg"])
        self.scroll_frame.configure(fg_color=theme["window_bg"])

        for frame in self._card_content_frames:
            frame.configure(fg_color=theme["card_bg"])
        for eyebrow in self._eyebrow_labels:
            eyebrow.configure(text_color=theme["accent"])

        self.title_label.configure(text_color=theme["ink"])

        for label in (
            self.error_correction_label, self.format_label, self.box_size_label,
            self.border_label, self.fill_color_label, self.back_color_label,
        ):
            label.configure(text_color=theme["muted"])

        for entry in (self.url_entry, self.box_size_entry, self.border_entry):
            entry.configure(
                fg_color=theme["entry_bg"], text_color=theme["entry_text"],
                border_color=theme["entry_border"],
            )

        for button in (self.theme_toggle_button, self.logo_button, self.save_button):
            button.configure(
                fg_color=theme["accent"], hover_color=theme["accent_hover"],
                text_color=theme["button_text"],
            )

        for secondary in (self.clear_button, self.logo_clear_button):
            secondary.configure(
                fg_color=theme["entry_bg"], hover_color=theme["entry_border"],
                text_color=theme["muted"],
            )

        for option_menu in (self.error_correction_menu, self.format_menu):
            option_menu.configure(
                fg_color=theme["entry_bg"], button_color=theme["accent"],
                button_hover_color=theme["accent_hover"], text_color=theme["ink"],
            )

        self.back_color_button.configure(border_color=theme["entry_border"])

        self.auto_favicon_checkbox.configure(text_color=theme["muted"])
        self.logo_hint_label.configure(text_color=theme["muted"])
        self.status_label.configure(text_color=theme["status_default"])
        self.preview_image_label.configure(text_color=theme["muted"])

    def on_toggle_theme(self) -> None:
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.current_theme = DARK_THEME
            self.theme_toggle_button.configure(text="☀️")
        else:
            self.current_theme = LIGHT_THEME
            self.theme_toggle_button.configure(text="🌙")
        self.apply_theme(self.current_theme)

    # ------------------------------------------------------------------
    # Style/logo event handlers
    # ------------------------------------------------------------------

    def on_choose_fill_color(self) -> None:
        chosen = colorchooser.askcolor(color=self.fill_color, title="Choose QR Color")
        hex_color = chosen[1]
        if hex_color:
            self.fill_color = hex_color
            self.fill_color_button.configure(fg_color=hex_color)
            self._schedule_auto_preview()

    def on_choose_back_color(self) -> None:
        chosen = colorchooser.askcolor(color=self.back_color, title="Choose Background Color")
        hex_color = chosen[1]
        if hex_color:
            self.back_color = hex_color
            self.back_color_button.configure(fg_color=hex_color)
            self._schedule_auto_preview()

    def on_choose_logo(self) -> None:
        self.auto_favicon_checkbox.deselect()
        chosen_path = filedialog.askopenfilename(title="Choose Logo Image", filetypes=self.LOGO_FILE_TYPES)
        if chosen_path:
            self.logo_path = Path(chosen_path)
            self.logo_hint_label.configure(
                text=f"Selected: {self.logo_path.name} (error correction will be forced to High)"
            )
            self._schedule_auto_preview()

    def on_clear_logo(self) -> None:
        self.logo_path = None
        self.auto_favicon_checkbox.deselect()
        self.logo_hint_label.configure(text="")
        self._schedule_auto_preview()

    def on_toggle_auto_favicon(self) -> None:
        if self.auto_favicon_checkbox.get():
            self.logo_path = None
            self.logo_hint_label.configure(
                text="Will fetch the website's favicon automatically "
                "(error correction will be forced to High)."
            )
        else:
            self.logo_hint_label.configure(text="")
        self._schedule_auto_preview()

    # ------------------------------------------------------------------
    # Auto-preview (debounced)
    # ------------------------------------------------------------------

    def _schedule_auto_preview(self) -> None:
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
        self._debounce_after_id = self.after(self.DEBOUNCE_MS, self._run_auto_preview)

    def _run_auto_preview(self) -> None:
        self._debounce_after_id = None
        self._generate_preview()

    # ------------------------------------------------------------------
    # Preview / Save / Clear flow
    # ------------------------------------------------------------------

    def _cleanup_pending(self) -> None:
        if self._pending_preview_path is not None:
            self._pending_preview_path.unlink(missing_ok=True)
        if self._pending_favicon_temp_path is not None:
            self._pending_favicon_temp_path.unlink(missing_ok=True)

        self._pending_preview_path = None
        self._pending_favicon_temp_path = None
        self._pending_logo_for_save = None
        self._pending_params = None

        self._current_preview_image = self._blank_preview_image
        self.preview_image_label.configure(
            image=self._current_preview_image,
            text="Type something and press Enter, or change a setting, to see a preview.",
        )
        self.save_button.configure(state="disabled")

    def on_clear_click(self) -> None:
        """Resets the entire form back to its default state."""
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
            self._debounce_after_id = None

        # Reset text input
        self.url_entry.delete(0, "end")

        # Reset style settings back to defaults
        self.error_correction_menu.set("Medium (~15%)")
        self.format_menu.set("PNG")
        self.box_size_entry.delete(0, "end")
        self.box_size_entry.insert(0, "10")
        self.border_entry.delete(0, "end")
        self.border_entry.insert(0, "4")

        self.fill_color = "#000000"
        self.fill_color_button.configure(fg_color=self.fill_color)
        self.back_color = "#FFFFFF"
        self.back_color_button.configure(fg_color=self.back_color)

        # Reset logo state, including the auto-fetch checkbox
        self.logo_path = None
        self.auto_favicon_checkbox.deselect()
        self.logo_hint_label.configure(text="")

        # Discard any pending preview and reset the preview area
        self._cleanup_pending()
        self.status_label.configure(text="")

    def _generate_preview(self) -> None:
        entered_text = self.url_entry.get()

        if not entered_text or not entered_text.strip():
            self._cleanup_pending()
            self.status_label.configure(text="")
            return

        try:
            box_size = int(self.box_size_entry.get())
            border = int(self.border_entry.get())
        except ValueError:
            self._cleanup_pending()
            self.status_label.configure(
                text="Error: Box size and border must be whole numbers.", text_color="red"
            )
            return

        self._cleanup_pending()

        error_correction = self.ERROR_CORRECTION_OPTIONS[self.error_correction_menu.get()]
        output_format = self.FORMAT_OPTIONS[self.format_menu.get()]

        logo_for_save = self.logo_path
        favicon_temp_path: Path | None = None

        if self.auto_favicon_checkbox.get():
            if not is_valid_http_url(entered_text.strip()):
                self.status_label.configure(
                    text="Error: Auto-fetch logo requires the text to be a valid URL.",
                    text_color="red",
                )
                return
            try:
                favicon_temp_path = fetch_favicon(entered_text.strip())
                logo_for_save = favicon_temp_path
            except FavIconFetchError as error:
                self.status_label.configure(text=f"Error: {error}", text_color="red")
                return

        if logo_for_save is not None and output_format is OutputFormat.SVG:
            self.status_label.configure(
                text="Error: Logo embedding is only supported for PNG, not SVG.",
                text_color="red",
            )
            if favicon_temp_path is not None:
                favicon_temp_path.unlink(missing_ok=True)
            return

        preview_temp = Path(tempfile.mktemp(suffix=".png", prefix="qr_preview_"))

        try:
            generate_qr_code(
                entered_text,
                preview_temp,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
                output_format=OutputFormat.PNG,
                fill_color=self.fill_color,
                back_color=self.back_color,
                logo_path=logo_for_save,
            )
        except QRGenerationError as error:
            self.status_label.configure(text=f"Error: {error}", text_color="red")
            if favicon_temp_path is not None:
                favicon_temp_path.unlink(missing_ok=True)
            return

        self._pending_preview_path = preview_temp
        self._pending_favicon_temp_path = favicon_temp_path
        self._pending_logo_for_save = logo_for_save
        self._pending_params = {
            "data": entered_text,
            "error_correction": error_correction,
            "box_size": box_size,
            "border": border,
            "output_format": output_format,
            "fill_color": self.fill_color,
            "back_color": self.back_color,
            "logo_path": logo_for_save,
        }

        preview_image = Image.open(preview_temp)
        self._current_preview_image = ctk.CTkImage(
            light_image=preview_image, dark_image=preview_image,
            size=(self.PREVIEW_SIZE, self.PREVIEW_SIZE),
        )
        self.preview_image_label.configure(image=self._current_preview_image, text="")

        self.save_button.configure(state="normal")
        self.status_label.configure(
            text="Preview ready. Click Save As to write it to a file.",
            text_color=self.current_theme["status_default"],
        )

    def on_save_click(self) -> None:
        """Saves the previewed QR code, then fully resets the form for the next one."""
        if self._pending_params is None:
            return

        output_format = self._pending_params["output_format"]
        output_path = self._ask_save_location(output_format)
        if output_path is None:
            return

        try:
            generate_qr_code(output_path=output_path, **self._pending_params)
        except QRGenerationError as error:
            self.status_label.configure(text=f"Error: {error}", text_color="red")
            self._cleanup_pending()
            return

        # Full reset on success — clears text, colors, logo, and the
        # auto-fetch checkbox, ready for the next QR code from a clean slate.
        self.on_clear_click()
        self.status_label.configure(text=f"QR code saved to {output_path}", text_color="green")
        
    def _ask_save_location(self, output_format: OutputFormat) -> Path | None:
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