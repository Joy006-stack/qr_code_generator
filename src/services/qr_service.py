from enum import Enum
from pathlib import Path

import qrcode
import qrcode.image.svg


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


def generate_qr_code(
    data: str,
    output_path: Path,
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.MEDIUM,
    box_size: int = 10,
    border: int = 4,
    output_format: OutputFormat = OutputFormat.PNG,
) -> Path:
    """
    Generate a QR code image from the given text/URL and save it to disk.

    Args:
        data: The text or URL to encode into the QR code.
        output_path: Full file path (including filename) where the image will be saved.
        error_correction: How much redundancy to embed for damage resistance.
        box_size: Pixel size of each QR module. Must be a positive integer.
        border: Width of the quiet zone border, in modules. QR spec minimum is 4.
        output_format: PNG or SVG.

    Returns:
        The path the QR code was saved to.

    Raises:
        QRGenerationError: If input is invalid, or the file cannot be saved.
    """
    if not data or not data.strip():
        raise QRGenerationError("Cannot generate a QR code from empty text.")

    if box_size < 1:
        raise QRGenerationError("Box size must be a positive integer.")

    if border < 0:
        raise QRGenerationError("Border cannot be negative.")

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
            image = qr.make_image(fill_color="black", back_color="white")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

    except OSError as error:
        raise QRGenerationError(f"Failed to save QR code: {error}") from error

    return output_path