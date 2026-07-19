from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.browse_filter import SORTS, filter_catalog
from app.widgets.movie_grid import MovieGrid


def _filter_field(label_text: str, field: QWidget) -> QVBoxLayout:
    column = QVBoxLayout()
    column.setSpacing(4)
    label = QLabel(label_text)
    label.setProperty("role", "muted")
    column.addWidget(label)
    column.addWidget(field)
    return column


class BrowseMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.library = library

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("Browse the catalog")
        title.setProperty("role", "h1")
        layout.addWidget(title)

        filters_card = QFrame()
        filters_card.setProperty("class", "card")
        filters = QVBoxLayout(filters_card)
        filters.setContentsMargins(20, 16, 20, 16)
        filters.setSpacing(14)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies & TV shows by title...")
        self.search_input.textChanged.connect(self._refresh)
        filters.addWidget(self.search_input)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(20)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Movie", "TV"])
        self.type_combo.currentTextChanged.connect(self._refresh)
        filter_row.addLayout(_filter_field("Type", self.type_combo))

        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Any")
        self.genre_combo.addItems(sorted({g for item in catalog.items for g in item["genres"]}))
        self.genre_combo.currentTextChanged.connect(self._refresh)
        filter_row.addLayout(_filter_field("Genre", self.genre_combo))

        self.year_from = QLineEdit()
        self.year_from.setPlaceholderText("Any")
        self.year_from.setFixedWidth(80)
        self.year_from.textChanged.connect(self._refresh)
        filter_row.addLayout(_filter_field("From year", self.year_from))

        self.year_to = QLineEdit()
        self.year_to.setPlaceholderText("Any")
        self.year_to.setFixedWidth(80)
        self.year_to.textChanged.connect(self._refresh)
        filter_row.addLayout(_filter_field("To year", self.year_to))

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(list(SORTS.keys()))
        self.sort_combo.currentTextChanged.connect(self._refresh)
        filter_row.addLayout(_filter_field("Sort", self.sort_combo))

        filter_row.addStretch()
        filters.addLayout(filter_row)
        layout.addWidget(filters_card)

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
            query=self.search_input.text(),
            media_type=media_type,
            genre=genre,
            year_from=self._year_value(self.year_from.text()),
            year_to=self._year_value(self.year_to.text()),
            exclude_keys=self.library.watched_keys,
            sort=self.sort_combo.currentText(),
        )
        self.grid.set_items(results)
