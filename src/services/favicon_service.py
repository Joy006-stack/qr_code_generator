import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

FAVICON_SERVICE_URL = "https://www.google.com/s2/favicons"
REQUEST_TIMEOUT_SECONDS = 5.0
MAX_CONTENT_BYTES = 2 * 1024 * 1024  # 2 MB — generous for a small favicon


class FavIconFetchError(Exception):
    """Raised when a website's favicon cannot be fetched or is invalid."""


def is_valid_http_url(text: str) -> bool:
    """
    Checks whether the given text is a well-formed http/https URL.

    Args:
        text: The text to check.

    Returns:
        True if text looks like a valid http(s) URL, False otherwise.
    """
    try:
        result = urlparse(text.strip())
    except ValueError:
        return False

    return result.scheme in ("http", "https") and bool(result.netloc)


def fetch_favicon(url: str, size: int = 128) -> Path:
    """
    Downloads the favicon for the given website URL and saves it to a
    temporary file.

    Args:
        url: The website URL to fetch a favicon for. Must be a valid http/https URL.
        size: Requested favicon size in pixels (the service may not honor this exactly).

    Returns:
        Path to a temporary PNG file containing the favicon.

    Raises:
        FavIconFetchError: If the URL is invalid, the request fails, times out,
            the response isn't a valid image, or it exceeds the size limit.
    """
    if not is_valid_http_url(url):
        raise FavIconFetchError(f"'{url}' is not a valid http/https URL.")

    domain = urlparse(url).netloc

    try:
        response = requests.get(
            FAVICON_SERVICE_URL,
            params={"domain": domain, "sz": size},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise FavIconFetchError(f"Network error fetching favicon: {error}") from error

    if response.status_code != 200:
        raise FavIconFetchError(
            f"Favicon service returned status {response.status_code}."
        )

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise FavIconFetchError(
            f"Favicon service did not return an image (got '{content_type}')."
        )

    if len(response.content) > MAX_CONTENT_BYTES:
        raise FavIconFetchError("Favicon response was unexpectedly large; aborting.")

    try:
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".png", delete=False, prefix="qr_favicon_"
        )
        temp_file.write(response.content)
        temp_file.close()
    except OSError as error:
        raise FavIconFetchError(f"Could not save favicon to disk: {error}") from error

    return Path(temp_file.name)