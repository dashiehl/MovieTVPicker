from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QScrollArea, QWidget

from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.widgets.movie_card import MovieCard

CARD_WIDTH = 184
COLUMN_SPACING = 16


class MovieGrid(QScrollArea):
    def __init__(self, image_loader: ImageLoader, library: LibraryStore, empty_message: str = "Nothing to show.", parent=None):
        super().__init__(parent)
        self.image_loader = image_loader
        self.library = library
        self.empty_message = empty_message
        self._cards: list[MovieCard] = []
        self._columns = 0

        self.setWidgetResizable(True)
        self.set_items([])

    def set_items(self, items: list[dict]) -> None:
        scroll_pos = self.verticalScrollBar().value()
        self._cards = [MovieCard(item, self.image_loader, self.library) for item in items]
        self._columns = max(1, self.viewport().width() // (CARD_WIDTH + COLUMN_SPACING))
        self._rebuild()
        self.verticalScrollBar().setValue(scroll_pos)

    def _rebuild(self) -> None:
        # QGridLayout keeps stale column-width metadata even after items are
        # taken out of it, so a changed column count needs a fresh layout
        # (and container) rather than reusing the old one — otherwise the
        # scroll area keeps sizing itself for the previous, wider layout.
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(COLUMN_SPACING)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        if not self._cards:
            empty_label = QLabel(self.empty_message)
            empty_label.setProperty("role", "empty-state")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setWordWrap(True)
            grid.addWidget(empty_label, 0, 0)
        else:
            columns = self._columns or 1
            for i, card in enumerate(self._cards):
                grid.addWidget(card, i // columns, i % columns)

        self.setWidget(container)  # takes ownership; old container is deleted

    def _reflow(self) -> None:
        if not self._cards:
            return
        columns = max(1, self.viewport().width() // (CARD_WIDTH + COLUMN_SPACING))
        if columns == self._columns:
            return
        self._columns = columns
        scroll_pos = self.verticalScrollBar().value()
        self._rebuild()
        self.verticalScrollBar().setValue(scroll_pos)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow()
