from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.browse_filter import SORTS, filter_catalog
from app.widgets.movie_grid import MovieGrid


class BrowseMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.library = library

        layout = QVBoxLayout(self)

        filters = QHBoxLayout()

        filters.addWidget(QLabel("Type"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Movie", "TV"])
        self.type_combo.currentTextChanged.connect(self._refresh)
        filters.addWidget(self.type_combo)

        filters.addWidget(QLabel("Genre"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Any")
        self.genre_combo.addItems(sorted({g for item in catalog.items for g in item["genres"]}))
        self.genre_combo.currentTextChanged.connect(self._refresh)
        filters.addWidget(self.genre_combo)

        filters.addWidget(QLabel("From year"))
        self.year_from = QLineEdit()
        self.year_from.setPlaceholderText("Any")
        self.year_from.setFixedWidth(70)
        self.year_from.textChanged.connect(self._refresh)
        filters.addWidget(self.year_from)

        filters.addWidget(QLabel("To year"))
        self.year_to = QLineEdit()
        self.year_to.setPlaceholderText("Any")
        self.year_to.setFixedWidth(70)
        self.year_to.textChanged.connect(self._refresh)
        filters.addWidget(self.year_to)

        filters.addWidget(QLabel("Sort"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(list(SORTS.keys()))
        self.sort_combo.currentTextChanged.connect(self._refresh)
        filters.addWidget(self.sort_combo)

        filters.addStretch()
        layout.addLayout(filters)

        self.grid = MovieGrid(image_loader, library, empty_message="No results match those filters.")
        layout.addWidget(self.grid)

        library.changed.connect(self._refresh)
        self._refresh()

    def _year_value(self, text: str) -> int | None:
        text = text.strip()
        return int(text) if text.isdigit() else None

    def _refresh(self) -> None:
        media_type = {"All": "all", "Movie": "movie", "TV": "tv"}[self.type_combo.currentText()]
        genre = "" if self.genre_combo.currentText() == "Any" else self.genre_combo.currentText()
        results = filter_catalog(
            self.catalog.items,
            media_type=media_type,
            genre=genre,
            year_from=self._year_value(self.year_from.text()),
            year_to=self._year_value(self.year_to.text()),
            exclude_keys=self.library.watched_keys,
            sort=self.sort_combo.currentText(),
        )
        self.grid.set_items(results)
