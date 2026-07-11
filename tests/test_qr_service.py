from pathlib import Path

import pytest
from PIL import Image

from src.services.qr_service import (
    ErrorCorrectionLevel,
    OutputFormat,
    QRGenerationError,
    generate_qr_code,
)


@pytest.fixture
def test_logo(tmp_path: Path) -> Path:
    """Creates a simple solid-color PNG to use as a logo in tests."""
    logo_path = tmp_path / "logo.png"
    image = Image.new("RGBA", (200, 200), (220, 38, 38, 255))
    image.save(logo_path)
    return logo_path


def test_generate_qr_code_creates_a_file(tmp_path: Path) -> None:
    """A valid input should produce a real PNG file at the given path."""
    output_path = tmp_path / "test_qr.png"
    result_path = generate_qr_code("https://example.com", output_path)
    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_qr_code_rejects_empty_string(tmp_path: Path) -> None:
    """Empty input should raise QRGenerationError and create no file."""
    output_path = tmp_path / "should_not_exist.png"
    with pytest.raises(QRGenerationError):
        generate_qr_code("", output_path)
    assert not output_path.exists()


def test_generate_qr_code_rejects_whitespace_only(tmp_path: Path) -> None:
    """Input that's only whitespace should be treated the same as empty."""
    with pytest.raises(QRGenerationError):
        generate_qr_code("   ", tmp_path / "should_not_exist.png")


def test_generate_qr_code_creates_missing_parent_folders(tmp_path: Path) -> None:
    """If the destination folder doesn't exist yet, it should be created automatically."""
    output_path = tmp_path / "nested" / "folders" / "qr.png"
    generate_qr_code("test data", output_path)
    assert output_path.exists()
    assert output_path.parent.is_dir()


@pytest.mark.parametrize(
    "level",
    [
        ErrorCorrectionLevel.LOW,
        ErrorCorrectionLevel.MEDIUM,
        ErrorCorrectionLevel.QUARTILE,
        ErrorCorrectionLevel.HIGH,
    ],
)
def test_generate_qr_code_accepts_all_error_correction_levels(
    tmp_path: Path, level: ErrorCorrectionLevel
) -> None:
    """Every ErrorCorrectionLevel option should produce a valid file without error."""
    output_path = tmp_path / f"qr_{level.name}.png"
    generate_qr_code("test data", output_path, error_correction=level)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_qr_code_rejects_box_size_zero(tmp_path: Path) -> None:
    """box_size of exactly 0 (the boundary) should be rejected."""
    with pytest.raises(QRGenerationError):
        generate_qr_code("test", tmp_path / "qr.png", box_size=0)


def test_generate_qr_code_accepts_box_size_one(tmp_path: Path) -> None:
    """box_size of exactly 1 (the smallest valid value) should succeed."""
    output_path = tmp_path / "qr.png"
    generate_qr_code("test", output_path, box_size=1)
    assert output_path.exists()


def test_generate_qr_code_rejects_negative_box_size(tmp_path: Path) -> None:
    """A clearly invalid negative box_size should be rejected."""
    with pytest.raises(QRGenerationError):
        generate_qr_code("test", tmp_path / "qr.png", box_size=-5)


def test_generate_qr_code_rejects_negative_border(tmp_path: Path) -> None:
    """A negative border should be rejected."""
    with pytest.raises(QRGenerationError):
        generate_qr_code("test", tmp_path / "qr.png", border=-1)


def test_generate_qr_code_accepts_border_zero(tmp_path: Path) -> None:
    """border of exactly 0 (the smallest valid value) should succeed."""
    output_path = tmp_path / "qr.png"
    generate_qr_code("test", output_path, border=0)
    assert output_path.exists()


def test_generate_qr_code_larger_box_size_produces_larger_file(tmp_path: Path) -> None:
    """A larger box_size should produce a visibly larger image file."""
    small_path = tmp_path / "small.png"
    large_path = tmp_path / "large.png"
    generate_qr_code("test data", small_path, box_size=2)
    generate_qr_code("test data", large_path, box_size=20)
    assert large_path.stat().st_size > small_path.stat().st_size


def test_generate_qr_code_svg_format_creates_svg_file(tmp_path: Path) -> None:
    """output_format=SVG should produce a real, non-empty SVG file."""
    output_path = tmp_path / "test_qr.svg"
    result_path = generate_qr_code(
        "https://example.com", output_path, output_format=OutputFormat.SVG
    )
    assert result_path == output_path
    assert output_path.exists()
    content = output_path.read_text()
    assert "<svg" in content.lower()


def test_generate_qr_code_accepts_high_contrast_colors(tmp_path: Path) -> None:
    """Genuinely high-contrast custom colors should succeed."""
    output_path = tmp_path / "colored.png"
    generate_qr_code(
        "test data", output_path, fill_color="#1E3A8A", back_color="#FEF3C7"
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_qr_code_rejects_low_contrast_colors(tmp_path: Path) -> None:
    """Colors too close in brightness should be rejected before saving."""
    output_path = tmp_path / "should_not_exist.png"
    with pytest.raises(QRGenerationError):
        generate_qr_code(
            "test", output_path, fill_color="#FFFF00", back_color="#FFFFCC"
        )
    assert not output_path.exists()


def test_generate_qr_code_rejects_invalid_hex_color(tmp_path: Path) -> None:
    """A malformed hex color string should raise a clear error, not crash unexpectedly."""
    with pytest.raises(QRGenerationError):
        generate_qr_code(
            "test", tmp_path / "qr.png", fill_color="not-a-color", back_color="#FFFFFF"
        )


def test_generate_qr_code_default_colors_are_black_and_white(tmp_path: Path) -> None:
    """Without specifying colors, behavior should match the original black-on-white default."""
    output_path = tmp_path / "default_colors.png"
    generate_qr_code("test data", output_path)
    assert output_path.exists()


# --- Phase 11: tests for logo embedding ---


def test_generate_qr_code_with_logo_creates_a_file(tmp_path: Path, test_logo: Path) -> None:
    """Providing a valid logo_path should succeed and produce a file."""
    output_path = tmp_path / "qr_with_logo.png"
    generate_qr_code(
        "https://example.com", output_path, logo_path=test_logo
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_qr_code_with_logo_forces_high_error_correction(
    tmp_path: Path, test_logo: Path
) -> None:
    """Even if LOW is requested, a logo should force HIGH error correction internally."""
    output_path = tmp_path / "qr_with_logo_low_requested.png"
    generate_qr_code(
        "https://example.com",
        output_path,
        error_correction=ErrorCorrectionLevel.LOW,
        logo_path=test_logo,
    )
    assert output_path.exists()


def test_generate_qr_code_rejects_svg_with_logo(tmp_path: Path, test_logo: Path) -> None:
    """SVG output combined with a logo should be explicitly rejected, not silently ignored."""
    output_path = tmp_path / "should_not_exist.svg"
    with pytest.raises(QRGenerationError):
        generate_qr_code(
            "test",
            output_path,
            logo_path=test_logo,
            output_format=OutputFormat.SVG,
        )
    assert not output_path.exists()


def test_generate_qr_code_rejects_invalid_logo_path(tmp_path: Path) -> None:
    """A logo_path pointing to a nonexistent or invalid file should raise a clear error."""
    output_path = tmp_path / "qr.png"
    fake_logo_path = tmp_path / "does_not_exist.png"
    with pytest.raises(QRGenerationError):
        generate_qr_code("test", output_path, logo_path=fake_logo_path)


def test_generate_qr_code_with_logo_is_larger_than_without(
    tmp_path: Path, test_logo: Path
) -> None:
    """A QR code with a logo embedded should differ in file size from one without."""
    no_logo_path = tmp_path / "no_logo.png"
    with_logo_path = tmp_path / "with_logo.png"
    generate_qr_code("https://example.com", no_logo_path)
    generate_qr_code("https://example.com", with_logo_path, logo_path=test_logo)
    assert no_logo_path.stat().st_size != with_logo_path.stat().st_size