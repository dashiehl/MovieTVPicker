from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app import db
from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.swipe_batch import pick_swipe_batch
from app.state import AppState
from app.theme import refresh_style
from app.utils import catalog_key
from app.widgets.swipe_deck import SwipeDeck

MEDIA_FILTERS = [("All", "all"), ("Movies", "movie"), ("TV Shows", "tv")]


class SwipeMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, state: AppState, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.image_loader = image_loader
        self.library = library
        self.state = state
        self.media_filter = "all"

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._deck: SwipeDeck | None = None

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label, value in MEDIA_FILTERS:
            btn = QPushButton(label)
            btn.setProperty("class", "filter-chip")
            btn.clicked.connect(lambda checked=False, v=value: self._set_media_filter(v))
            filter_row.addWidget(btn)
            self._filter_buttons[value] = btn
        self._layout.addLayout(filter_row)
        self._refresh_filter_buttons()

        self._restart_note = QLabel("You've swiped through everything — starting over from the top!")
        self._restart_note.setProperty("role", "muted")
        self._restart_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._restart_note.hide()
        self._layout.addWidget(self._restart_note)

        self._status_label = QLabel()
        self._status_label.setProperty("role", "empty-state")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._status_label)

        self._reload_btn = QPushButton("Load more")
        self._reload_btn.setProperty("class", "btn")
        self._reload_btn.clicked.connect(self.load_batch)
        self._layout.addWidget(self._reload_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.load_batch()

    def _set_media_filter(self, value: str) -> None:
        if value == self.media_filter:
            return
        self.media_filter = value
        self._refresh_filter_buttons()
        self.load_batch()

    def _refresh_filter_buttons(self) -> None:
        for value, btn in self._filter_buttons.items():
            btn.setProperty("active", value == self.media_filter)
            refresh_style(btn)

    def load_batch(self) -> None:
        if self._deck is not None:
            self._layout.removeWidget(self._deck)
            self._deck.deleteLater()
            self._deck = None

        swipes = db.get_swipes(self.state.solo_profile)
        exclude_keys = self.library.watched_keys | {catalog_key(s) for s in swipes}
        batch = pick_swipe_batch(self.catalog.items, exclude_keys, media_type=self.media_filter)

        restarted = False
        if not batch and swipes:
            # Nothing left to swipe on because we've swiped everything the catalog has
            # to offer for this filter (not because the catalog itself is empty) — clear
            # this profile's swipe history and go through it again, minus watched items.
            db.clear_swipes(self.state.solo_profile)
            batch = pick_swipe_batch(self.catalog.items, self.library.watched_keys, media_type=self.media_filter)
            restarted = True

        self._restart_note.setVisible(restarted)

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
        self._layout.insertWidget(2, self._deck)

    def _on_swipe(self, item: dict, liked: bool) -> None:
        db.record_swipe(item["id"], item["mediaType"], self.state.solo_profile, liked)

    def _on_finished(self) -> None:
        self._status_label.setText("That's the whole batch!")
        self._status_label.show()
        self._reload_btn.show()
