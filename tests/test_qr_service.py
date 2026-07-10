from pathlib import Path

import pytest

from src.services.qr_service import (
    ErrorCorrectionLevel,
    OutputFormat,
    QRGenerationError,
    generate_qr_code,
)


def test_generate_qr_code_creates_a_file(tmp_path: Path) -> None:
    """A valid input should produce a real PNG file at the given path."""
    # Arrange
    output_path = tmp_path / "test_qr.png"

    # Act
    result_path = generate_qr_code("https://example.com", output_path)

    # Assert
    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_qr_code_rejects_empty_string(tmp_path: Path) -> None:
    """Empty input should raise QRGenerationError and create no file."""
    # Arrange
    output_path = tmp_path / "should_not_exist.png"

    # Act & Assert
    with pytest.raises(QRGenerationError):
        generate_qr_code("", output_path)

    assert not output_path.exists()


def test_generate_qr_code_rejects_whitespace_only(tmp_path: Path) -> None:
    """Input that's only whitespace should be treated the same as empty."""
    with pytest.raises(QRGenerationError):
        generate_qr_code("   ", tmp_path / "should_not_exist.png")


def test_generate_qr_code_creates_missing_parent_folders(tmp_path: Path) -> None:
    """If the destination folder doesn't exist yet, it should be created automatically."""
    # Arrange: a path with nested folders that don't exist yet
    output_path = tmp_path / "nested" / "folders" / "qr.png"

    # Act
    generate_qr_code("test data", output_path)

    # Assert
    assert output_path.exists()
    assert output_path.parent.is_dir()


# --- Phase 9: tests for error correction, size, border, and format ---


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
    # Arrange
    output_path = tmp_path / f"qr_{level.name}.png"

    # Act
    generate_qr_code("test data", output_path, error_correction=level)

    # Assert
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
    # Arrange
    small_path = tmp_path / "small.png"
    large_path = tmp_path / "large.png"

    # Act
    generate_qr_code("test data", small_path, box_size=2)
    generate_qr_code("test data", large_path, box_size=20)

    # Assert: a bigger rendered image should mean a bigger file on disk
    assert large_path.stat().st_size > small_path.stat().st_size


def test_generate_qr_code_svg_format_creates_svg_file(tmp_path: Path) -> None:
    """output_format=SVG should produce a real, non-empty SVG file."""
    # Arrange
    output_path = tmp_path / "test_qr.svg"

    # Act
    result_path = generate_qr_code(
        "https://example.com", output_path, output_format=OutputFormat.SVG
    )

    # Assert
    assert result_path == output_path
    assert output_path.exists()
    content = output_path.read_text()
    assert "<svg" in content.lower()