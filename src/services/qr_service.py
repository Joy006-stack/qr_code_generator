from pathlib import Path

import qrcode


class QRGenerationError(Exception):
    """Raised when QR code generation or saving fails."""


def generate_qr_code(data: str, output_path: Path) -> Path:
    """
    Generate a QR code image from the given text/URL and save it to disk.

    Args:
        data: The text or URL to encode into the QR code.
        output_path: Full file path (including filename) where the PNG will be saved.

    Returns:
        The path the QR code was saved to.

    Raises:
        QRGenerationError: If the input is empty or the file cannot be saved.
    """
    if not data or not data.strip():
        raise QRGenerationError("Cannot generate a QR code from empty text.")

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data.strip())
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

    except OSError as error:
        raise QRGenerationError(f"Failed to save QR code: {error}") from error

    return output_path