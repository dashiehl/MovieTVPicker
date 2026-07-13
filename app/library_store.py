"""Shared watchlist/watched state so every page/card can check status and
mutate without duplicating db.py calls. Emits `changed` after any mutation
so visible widgets can refresh their button/border states."""

from PySide6.QtCore import QObject, Signal

from app import db
from app.utils import catalog_key


class LibraryStore(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.watchlist: list[dict] = []
        self.watched: list[dict] = []
        self.refresh()

    def refresh(self) -> None:
        self.watchlist = db.get_watchlist()
        self.watched = db.get_watched()
        self.changed.emit()

    @property
    def watchlist_keys(self) -> set[str]:
        return {catalog_key(i) for i in self.watchlist}

    @property
    def watched_keys(self) -> set[str]:
        return {catalog_key(i) for i in self.watched}

    def add_to_watchlist(self, item: dict) -> None:
        db.add_to_watchlist(_to_record_payload(item))
        self.refresh()

    def remove_from_watchlist(self, record_id: str) -> None:
        db.remove_from_watchlist(record_id)
        self.refresh()

    def mark_watched(self, item: dict) -> None:
        db.mark_watched(_to_record_payload(item))
        self.refresh()

    def remove_from_watched(self, record_id: str) -> None:
        db.remove_from_watched(record_id)
        self.refresh()


def _to_record_payload(item: dict) -> dict:
    """Catalog items use 'id'; watchlist/watched records store it as 'catalogId'
    (their own 'id' is the record's own UUID) — prefer 'catalogId' when present."""
    return {
        "catalogId": item.get("catalogId", item.get("id")),
        "mediaType": item["mediaType"],
        "title": item["title"],
        "posterPath": item.get("posterPath"),
        "year": item.get("year"),
        "genres": item.get("genres", []),
    }
