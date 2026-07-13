from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.widgets.movie_grid import MovieGrid


class SearchPage(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog

        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies & TV shows...")
        self.search_input.textChanged.connect(self._on_query_changed)
        layout.addWidget(self.search_input)

        self.grid = MovieGrid(
            image_loader, library,
            empty_message="Search for a movie or TV show to add it to your watchlist or watched history.",
        )
        layout.addWidget(self.grid)

    def _on_query_changed(self, text: str) -> None:
        query = text.strip().lower()
        if not query:
            self.grid.empty_message = "Search for a movie or TV show to add it to your watchlist or watched history."
            self.grid.set_items([])
            return
        results = [item for item in self.catalog.items if query in item["title"].lower()]
        self.grid.empty_message = "No matches in the catalog."
        self.grid.set_items(results)
