from pathlib import Path

import pytest

from src.services.history_service import (
    HistoryEntry,
    HistoryError,
    add_history_entry,
    clear_history,
    delete_history_entry,
    load_history,
)


def make_entry(data: str = "https://example.com") -> HistoryEntry:
    """Helper to build a simple test HistoryEntry without repeating every field."""
    return HistoryEntry(
        data=data,
        output_path="output/test_qr.png",
        output_format="png",
        fill_color="#000000",
        back_color="#FFFFFF",
        error_correction="Medium (~15%)",
    )


def test_load_history_returns_empty_list_when_no_file_exists(tmp_path: Path) -> None:
    """A fresh install with no history file should return an empty list, not error."""
    history_path = tmp_path / "history.json"
    assert load_history(history_path) == []


def test_add_history_entry_creates_file_and_saves_entry(tmp_path: Path) -> None:
    """Adding an entry should create the file and make it loadable afterward."""
    history_path = tmp_path / "history.json"
    entry = make_entry()

    add_history_entry(entry, history_path)

    assert history_path.exists()
    loaded = load_history(history_path)
    assert len(loaded) == 1
    assert loaded[0].data == "https://example.com"


def test_add_history_entry_puts_newest_first(tmp_path: Path) -> None:
    """Each new entry should be added to the FRONT of the list, not the back."""
    history_path = tmp_path / "history.json"

    add_history_entry(make_entry("first"), history_path)
    add_history_entry(make_entry("second"), history_path)

    loaded = load_history(history_path)
    assert loaded[0].data == "second"
    assert loaded[1].data == "first"


def test_add_history_entry_respects_max_limit(tmp_path: Path) -> None:
    """History should never grow beyond MAX_HISTORY_ENTRIES."""
    history_path = tmp_path / "history.json"

    for i in range(105):
        add_history_entry(make_entry(f"entry-{i}"), history_path)

    loaded = load_history(history_path)
    assert len(loaded) == 100
    # The most recent 100 should be kept — entry-104 down to entry-5.
    assert loaded[0].data == "entry-104"


def test_load_history_raises_on_corrupted_file(tmp_path: Path) -> None:
    """A file with invalid JSON should raise HistoryError, not crash unexpectedly."""
    history_path = tmp_path / "history.json"
    history_path.write_text("this is not valid json{{{", encoding="utf-8")

    with pytest.raises(HistoryError):
        load_history(history_path)


def test_clear_history_removes_the_file(tmp_path: Path) -> None:
    """Clearing history should leave no entries and no error on next load."""
    history_path = tmp_path / "history.json"
    add_history_entry(make_entry(), history_path)

    clear_history(history_path)

    assert load_history(history_path) == []


def test_clear_history_on_nonexistent_file_does_not_error(tmp_path: Path) -> None:
    """Clearing history that was never created should be a harmless no-op."""
    history_path = tmp_path / "history.json"
    clear_history(history_path)  # should not raise


def test_delete_history_entry_removes_only_that_entry(tmp_path: Path) -> None:
    """Deleting one entry by index should leave the others intact."""
    history_path = tmp_path / "history.json"
    add_history_entry(make_entry("first"), history_path)
    add_history_entry(make_entry("second"), history_path)
    add_history_entry(make_entry("third"), history_path)

    # loaded order is: third, second, first (index 0, 1, 2)
    delete_history_entry(1, history_path)  # removes "second"

    loaded = load_history(history_path)
    assert [entry.data for entry in loaded] == ["third", "first"]


def test_delete_history_entry_rejects_invalid_index(tmp_path: Path) -> None:
    """An out-of-range index should raise a clear error, not crash or silently do nothing."""
    history_path = tmp_path / "history.json"
    add_history_entry(make_entry(), history_path)

    with pytest.raises(HistoryError):
        delete_history_entry(5, history_path)