"""Loads the local movie/TV catalog (data/catalog.json) into memory.

Item shape (kept identical to the original JSON, camelCase and all):
{id, mediaType, title, year, genres, posterPath, overview}
"""

import json

from PySide6.QtCore import QObject, Signal

from app.config import CATALOG_PATH


class CatalogStore(QObject):
    loaded = Signal()
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.items: list[dict] = []
        self.updated_at: str | None = None

    def load(self) -> None:
        if not CATALOG_PATH.exists():
            self.error.emit(
                f"No catalog found at {CATALOG_PATH}. Run 'python scripts/build_catalog.py' "
                "or use the Rebuild button in Settings."
            )
            return
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            self.error.emit(f"Couldn't read the catalog file: {exc}")
            return

        self.items = data.get("items", [])
        self.updated_at = data.get("updatedAt")
        self.loaded.emit()

    def genres_for(self, media_type: str) -> list[str]:
        genres = set()
        for item in self.items:
            if item["mediaType"] == media_type:
                genres.update(item["genres"])
        return sorted(genres)
