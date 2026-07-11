from enum import Enum
from pathlib import Path

import qrcode
import qrcode.image.svg
from PIL import Image


class QRGenerationError(Exception):
    """Raised when QR code generation or saving fails."""


class ErrorCorrectionLevel(Enum):
    """
    QR code error correction levels.

    Higher levels mean the QR code can still be read even if partially
    damaged or obscured, at the cost of a denser (more complex) code.
    """

    LOW = qrcode.constants.ERROR_CORRECT_L        # ~7% recovery
    MEDIUM = qrcode.constants.ERROR_CORRECT_M      # ~15% recovery
    QUARTILE = qrcode.constants.ERROR_CORRECT_Q    # ~25% recovery
    HIGH = qrcode.constants.ERROR_CORRECT_H        # ~30% recovery


class OutputFormat(Enum):
    """Supported output image formats."""

    PNG = "png"
    SVG = "svg"


MAX_LOGO_SIZE_RATIO = 0.22


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string like '#RRGGBB' into an (r, g, b) tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise QRGenerationError(f"Invalid hex color: '{hex_color}'")
    try:
        return tuple(int(hex_color[i : i + 2], 16) for i in range(0, 6, 2))
    except ValueError as error:
        raise QRGenerationError(f"Invalid hex color: '{hex_color}'") from error


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Rough perceived brightness of an RGB color, from 0 (black) to 255 (white)."""
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def _colors_have_low_contrast(fill_color: str, back_color: str) -> bool:
    """
    Basic heuristic: if the foreground and background brightness are too
    close together, the QR code will likely be hard or impossible to scan.
    """
    fill_luminance = _relative_luminance(_hex_to_rgb(fill_color))
    back_luminance = _relative_luminance(_hex_to_rgb(back_color))
    return abs(fill_luminance - back_luminance) < 80


def _embed_logo(qr_image: Image.Image, logo_path: Path) -> Image.Image:
    """
    Pastes a logo image centered on top of the given QR code image.
    """
    try:
        logo = Image.open(logo_path).convert("RGBA")
    except (OSError, ValueError) as error:
        raise QRGenerationError(f"Could not open logo image: {error}") from error

    qr_image = qr_image.convert("RGBA")
    qr_width, qr_height = qr_image.size

    max_logo_width = int(qr_width * MAX_LOGO_SIZE_RATIO)
    max_logo_height = int(qr_height * MAX_LOGO_SIZE_RATIO)
    logo.thumbnail((max_logo_width, max_logo_height))

    position = (
        (qr_width - logo.width) // 2,
        (qr_height - logo.height) // 2,
    )

    qr_image.paste(logo, position, mask=logo)

    return qr_image


def generate_qr_code(
    data: str,
    output_path: Path,
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.MEDIUM,
    box_size: int = 10,
    border: int = 4,
    output_format: OutputFormat = OutputFormat.PNG,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    logo_path: Path | None = None,
) -> Path:
    """
    Generate a QR code image from the given text/URL and save it to disk.
    """
    if not data or not data.strip():
        raise QRGenerationError("Cannot generate a QR code from empty text.")

    if box_size < 1:
        raise QRGenerationError("Box size must be a positive integer.")

    if border < 0:
        raise QRGenerationError("Border cannot be negative.")

    if _colors_have_low_contrast(fill_color, back_color):
        raise QRGenerationError(
            "Foreground and background colors are too similar to scan reliably. "
            "Choose colors with more contrast."
        )

    if logo_path is not None and output_format is OutputFormat.SVG:
        raise QRGenerationError(
            "Logo embedding is only supported for PNG output, not SVG."
        )

    if logo_path is not None:
        error_correction = ErrorCorrectionLevel.HIGH

    try:
        if output_format is OutputFormat.SVG:
            image = qrcode.make(
                data.strip(),
                image_factory=qrcode.image.svg.SvgPathImage,
                error_correction=error_correction.value,
                box_size=box_size,
                border=border,
            )
        else:
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction.value,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data.strip())
            qr.make(fit=True)
            image = qr.make_image(fill_color=fill_color, back_color=back_color)

            if logo_path is not None:
                image = _embed_logo(image, logo_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

    except OSError as error:
        raise QRGenerationError(f"Failed to save QR code: {error}") from error

    return output_path