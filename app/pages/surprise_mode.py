import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.utils import catalog_key
from app.widgets.movie_card import MovieCard


class SurpriseMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.image_loader = image_loader
        self.library = library
        self._card: MovieCard | None = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._empty_label = QLabel("Click below for a random pick.")
        self._empty_label.setProperty("role", "empty-state")
        layout.addWidget(self._empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._card_slot = QVBoxLayout()
        layout.addLayout(self._card_slot)

        self.reroll_btn = QPushButton("Surprise me")
        self.reroll_btn.setProperty("class", "btn")
        self.reroll_btn.setFixedWidth(200)
        self.reroll_btn.clicked.connect(self.reroll)
        layout.addWidget(self.reroll_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def reroll(self) -> None:
        candidates = [item for item in self.catalog.items if catalog_key(item) not in self.library.watched_keys]
        if self._card is not None:
            self._card_slot.removeWidget(self._card)
            self._card.deleteLater()
            self._card = None

        if not candidates:
            self._empty_label.setText("No candidates available right now.")
            self._empty_label.show()
            return

        pick = random.choice(candidates)
        self._empty_label.hide()
        self._card = MovieCard(pick, self.image_loader, self.library)
        self._card_slot.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.reroll_btn.setText("Reroll")
