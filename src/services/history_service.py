import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

HISTORY_FILE_PATH = Path("logs") / "history.json"
MAX_HISTORY_ENTRIES = 100


class HistoryError(Exception):
    """Raised when history entries cannot be read from or written to disk."""


@dataclass
class HistoryEntry:
    """One past QR code generation, as recorded in history."""

    data: str
    output_path: str
    output_format: str
    fill_color: str
    back_color: str
    error_correction: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(raw: dict) -> "HistoryEntry":
        return HistoryEntry(
            data=raw["data"],
            output_path=raw["output_path"],
            output_format=raw["output_format"],
            fill_color=raw["fill_color"],
            back_color=raw["back_color"],
            error_correction=raw["error_correction"],
            timestamp=raw.get("timestamp", ""),
        )


def load_history(history_path: Path = HISTORY_FILE_PATH) -> list[HistoryEntry]:
    """
    Loads all saved history entries from disk.

    Args:
        history_path: Path to the history JSON file.

    Returns:
        A list of HistoryEntry objects, most recent first. Empty list if
        no history file exists yet.

    Raises:
        HistoryError: If the file exists but contains invalid/corrupted data.
    """
    if not history_path.exists():
        return []

    try:
        raw_text = history_path.read_text(encoding="utf-8")
        raw_entries = json.loads(raw_text)
        return [HistoryEntry.from_dict(entry) for entry in raw_entries]
    except (json.JSONDecodeError, KeyError, OSError) as error:
        raise HistoryError(f"Could not read history file: {error}") from error


def add_history_entry(entry: HistoryEntry, history_path: Path = HISTORY_FILE_PATH) -> None:
    """
    Adds a new entry to the top of the history list and saves it to disk.

    Older entries beyond MAX_HISTORY_ENTRIES are dropped, so the file
    doesn't grow unbounded over time.

    Args:
        entry: The HistoryEntry to record.
        history_path: Path to the history JSON file.

    Raises:
        HistoryError: If the history file cannot be written.
    """
    existing = load_history(history_path)
    updated = [entry] + existing
    updated = updated[:MAX_HISTORY_ENTRIES]

    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        raw_entries = [item.to_dict() for item in updated]
        history_path.write_text(
            json.dumps(raw_entries, indent=2), encoding="utf-8"
        )
    except OSError as error:
        raise HistoryError(f"Could not save history file: {error}") from error


def clear_history(history_path: Path = HISTORY_FILE_PATH) -> None:
    """Deletes all history entries."""
    if history_path.exists():
        try:
            history_path.unlink()
        except OSError as error:
            raise HistoryError(f"Could not clear history file: {error}") from error


def delete_history_entry(index: int, history_path: Path = HISTORY_FILE_PATH) -> None:
    """
    Removes a single entry from history by its position (0 = most recent).

    Raises:
        HistoryError: If the index is out of range or the file can't be saved.
    """
    entries = load_history(history_path)
    if index < 0 or index >= len(entries):
        raise HistoryError(f"No history entry at index {index}.")

    del entries[index]

    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        raw_entries = [item.to_dict() for item in entries]
        history_path.write_text(
            json.dumps(raw_entries, indent=2), encoding="utf-8"
        )
    except OSError as error:
        raise HistoryError(f"Could not save history file: {error}") from error