from pathlib import Path

import pytest

from src.services.qr_service import QRGenerationError, generate_qr_code


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