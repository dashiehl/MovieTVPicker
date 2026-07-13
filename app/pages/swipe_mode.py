from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app import db
from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.swipe_batch import pick_swipe_batch
from app.state import AppState
from app.utils import catalog_key
from app.widgets.swipe_deck import SwipeDeck


class SwipeMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, state: AppState, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.image_loader = image_loader
        self.library = library
        self.state = state

        self._layout = QVBoxLayout(self)
        self._deck: SwipeDeck | None = None

        self._status_label = QLabel()
        self._status_label.setProperty("role", "empty-state")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._status_label)

        self._reload_btn = QPushButton("Load more")
        self._reload_btn.setProperty("class", "btn")
        self._reload_btn.clicked.connect(self.load_batch)
        self._layout.addWidget(self._reload_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.load_batch()

    def load_batch(self) -> None:
        if self._deck is not None:
            self._layout.removeWidget(self._deck)
            self._deck.deleteLater()
            self._deck = None

        swipes = db.get_swipes(self.state.solo_profile)
        exclude_keys = self.library.watched_keys | {catalog_key(s) for s in swipes}
        batch = pick_swipe_batch(self.catalog.items, exclude_keys)

        if not batch:
            self._status_label.setText("You're all caught up — nothing new to swipe on right now.")
            self._status_label.show()
            self._reload_btn.show()
            return

        self._status_label.hide()
        self._reload_btn.hide()
        self._deck = SwipeDeck(batch, self.image_loader, self.library)
        self._deck.swiped.connect(self._on_swipe)
        self._deck.finished.connect(self._on_finished)
        self._layout.insertWidget(0, self._deck)

    def _on_swipe(self, item: dict, liked: bool) -> None:
        db.record_swipe(item["id"], item["mediaType"], self.state.solo_profile, liked)

    def _on_finished(self) -> None:
        self._status_label.setText("That's the whole batch!")
        self._status_label.show()
        self._reload_btn.show()
