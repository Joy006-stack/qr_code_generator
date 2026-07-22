import customtkinter as ctk


class Tooltip:
    """
    A simple hover tooltip for any CustomTkinter widget.

    Usage:
        Tooltip(some_button, "This button does X (Ctrl+X)")
    """

    def __init__(self, widget: ctk.CTkBaseClass, text: str, delay_ms: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._tooltip_window: ctk.CTkToplevel | None = None

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, event) -> None:
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, event) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self) -> None:
        if self._tooltip_window is not None:
            return

        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self._tooltip_window = ctk.CTkToplevel(self.widget)
        self._tooltip_window.overrideredirect(True)
        self._tooltip_window.geometry(f"+{x}+{y}")
        self._tooltip_window.attributes("-topmost", True)

        label = ctk.CTkLabel(
            self._tooltip_window,
            text=self.text,
            fg_color="#1A1A24",
            text_color="#F2F2F7",
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            padx=8,
            pady=4,
        )
        label.pack()

    def _hide(self) -> None:
        if self._tooltip_window is not None:
            self._tooltip_window.destroy()
            self._tooltip_window = None