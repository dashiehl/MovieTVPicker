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

        self.setWidgetResizable(True)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(COLUMN_SPACING)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self.set_items([])

    def set_items(self, items: list[dict]) -> None:
        # Every child (including any previous empty-state label) gets deleteLater()'d
        # here, so a fresh label is built below rather than reusing a persisted one —
        # reusing one across multiple clear cycles crashes once Qt actually deletes it.
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            empty_label = QLabel(self.empty_message)
            empty_label.setProperty("role", "empty-state")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(empty_label, 0, 0)
            return

        columns = max(1, (self.viewport().width() or 900) // (CARD_WIDTH + COLUMN_SPACING))
        for i, item in enumerate(items):
            card = MovieCard(item, self.image_loader, self.library)
            self._grid.addWidget(card, i // columns, i % columns)
