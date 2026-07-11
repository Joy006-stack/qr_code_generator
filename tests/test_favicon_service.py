from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.services.favicon_service import (
    FavIconFetchError,
    fetch_favicon,
    is_valid_http_url,
)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com", True),
        ("http://example.com", True),
        ("not a url at all", False),
        ("ftp://example.com", False),
        ("https://", False),
        ("", False),
    ],
)
def test_is_valid_http_url(url: str, expected: bool) -> None:
    """Only well-formed http/https URLs should be considered valid."""
    assert is_valid_http_url(url) is expected


@patch("src.services.favicon_service.requests.get")
def test_fetch_favicon_saves_successful_response(mock_get: Mock) -> None:
    """A successful, valid image response should be saved to a temp file."""
    # Arrange: fake a successful response with fake PNG bytes
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "image/png"}
    mock_response.content = b"fake-png-bytes"
    mock_get.return_value = mock_response

    # Act
    result_path = fetch_favicon("https://example.com")

    # Assert
    assert result_path.exists()
    assert result_path.read_bytes() == b"fake-png-bytes"
    result_path.unlink()  # clean up the temp file this test created


@patch("src.services.favicon_service.requests.get")
def test_fetch_favicon_rejects_non_200_status(mock_get: Mock) -> None:
    """A non-200 response should raise FavIconFetchError."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    with pytest.raises(FavIconFetchError):
        fetch_favicon("https://example.com")


@patch("src.services.favicon_service.requests.get")
def test_fetch_favicon_rejects_non_image_content_type(mock_get: Mock) -> None:
    """A response claiming to be something other than an image should be rejected."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_get.return_value = mock_response

    with pytest.raises(FavIconFetchError):
        fetch_favicon("https://example.com")


@patch("src.services.favicon_service.requests.get")
def test_fetch_favicon_rejects_oversized_content(mock_get: Mock) -> None:
    """A response larger than the size limit should be rejected."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "image/png"}
    mock_response.content = b"x" * (3 * 1024 * 1024)  # 3 MB, over our 2 MB limit
    mock_get.return_value = mock_response

    with pytest.raises(FavIconFetchError):
        fetch_favicon("https://example.com")


def test_fetch_favicon_rejects_invalid_url() -> None:
    """An invalid URL should be rejected before any network call is attempted."""
    with pytest.raises(FavIconFetchError):
        fetch_favicon("not a real url")