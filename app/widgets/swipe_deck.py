from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.utils import catalog_key

POSTER_SIZE = (280, 400)


class SwipeDeck(QWidget):
    """Single-card swipe UI shared by solo and group swipe modes.

    `items` is the fixed batch to swipe through; `swiped(item, liked)` fires
    per card, `finished()` fires once the batch is exhausted.
    """

    swiped = Signal(dict, bool)
    finished = Signal()

    def __init__(self, items: list[dict], image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.items = items
        self.image_loader = image_loader
        self.library = library
        self.index = 0

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.participant_banner = QFrame()
        self.participant_banner.setProperty("class", "banner-warning")
        banner_layout = QVBoxLayout(self.participant_banner)
        self.participant_label = QLabel()
        banner_layout.addWidget(self.participant_label)
        self.participant_banner.hide()
        outer.addWidget(self.participant_banner)

        card = QFrame()
        card.setProperty("class", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 12)
        card_layout.setSpacing(8)

        self.poster_label = QLabel()
        self.poster_label.setFixedSize(*POSTER_SIZE)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setWordWrap(True)
        card_layout.addWidget(self.poster_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QLabel()
        self.title_label.setProperty("role", "h2")
        self.title_label.setWordWrap(True)
        self.title_label.setContentsMargins(16, 0, 16, 0)
        card_layout.addWidget(self.title_label)

        self.meta_label = QLabel()
        self.meta_label.setProperty("role", "muted")
        self.meta_label.setContentsMargins(16, 0, 16, 0)
        card_layout.addWidget(self.meta_label)

        actions = QHBoxLayout()
        actions.setContentsMargins(16, 4, 16, 0)
        self.watchlist_btn = QPushButton()
        self.watchlist_btn.setProperty("class", "card-action")
        self.watchlist_btn.clicked.connect(self._add_current_to_watchlist)
        self.watched_btn = QPushButton()
        self.watched_btn.setProperty("class", "card-action")
        self.watched_btn.clicked.connect(self._mark_current_watched)
        actions.addWidget(self.watchlist_btn)
        actions.addWidget(self.watched_btn)
        card_layout.addLayout(actions)

        card.setFixedWidth(POSTER_SIZE[0] + 32)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        swipe_actions = QHBoxLayout()
        swipe_actions.setSpacing(24)
        self.pass_btn = QPushButton("✕")
        self.pass_btn.setFixedSize(64, 64)
        self.pass_btn.setProperty("class", "card-action")
        self.pass_btn.clicked.connect(lambda: self._handle_choice(False))
        self.like_btn = QPushButton("♥")
        self.like_btn.setFixedSize(64, 64)
        self.like_btn.setProperty("class", "btn")
        self.like_btn.clicked.connect(lambda: self._handle_choice(True))
        swipe_actions.addStretch()
        swipe_actions.addWidget(self.pass_btn)
        swipe_actions.addWidget(self.like_btn)
        swipe_actions.addStretch()
        outer.addSpacing(12)
        outer.addLayout(swipe_actions)

        self.empty_label = QLabel("No more cards in this batch.")
        self.empty_label.setProperty("role", "empty-state")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.empty_label)

        self._card = card
        self._swipe_actions_widget = swipe_actions

        self.library.changed.connect(self._refresh_actions)
        self._render()

    def set_participant_label(self, name: str | None) -> None:
        if name:
            remaining = len(self.items) - self.index
            self.participant_label.setText(f"{name}'s turn — {remaining} card(s) left")
            self.participant_banner.show()
        else:
            self.participant_banner.hide()

    def _current_item(self) -> dict | None:
        if self.index >= len(self.items):
            return None
        return self.items[self.index]

    def _render(self) -> None:
        item = self._current_item()
        finished = item is None
        self._card.setVisible(not finished)
        self.empty_label.setVisible(finished)
        self.pass_btn.setVisible(not finished)
        self.like_btn.setVisible(not finished)
        if finished:
            self.participant_banner.hide()
            return

        self.image_loader.load(item.get("posterPath"), self._set_pixmap)
        self.title_label.setText(item["title"])
        media_label = "TV" if item["mediaType"] == "tv" else "Movie"
        self.meta_label.setText(f"{item.get('year') or 'Unknown year'} · {media_label}")
        self._refresh_actions()

        # re-issue the participant banner text (card index moved)
        current_text = self.participant_label.text()
        if current_text:
            name = current_text.split("'s turn")[0]
            self.set_participant_label(name)

    def _set_pixmap(self, pixmap) -> None:
        if pixmap is None:
            self.poster_label.setText(self._current_item()["title"] if self._current_item() else "")
            return
        scaled = pixmap.scaled(
            *POSTER_SIZE, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )
        self.poster_label.setPixmap(scaled)

    def _refresh_actions(self) -> None:
        item = self._current_item()
        if item is None:
            return
        key = catalog_key(item)
        in_watchlist = key in self.library.watchlist_keys
        is_watched = key in self.library.watched_keys
        self.watchlist_btn.setText("In watchlist" if in_watchlist else "+ Watchlist")
        self.watchlist_btn.setDisabled(in_watchlist)
        self.watched_btn.setText("Watched" if is_watched else "Mark watched")
        self.watched_btn.setDisabled(is_watched)

    def _add_current_to_watchlist(self) -> None:
        item = self._current_item()
        if item is not None:
            self.library.add_to_watchlist(item)

    def _mark_current_watched(self) -> None:
        item = self._current_item()
        if item is not None:
            self.library.mark_watched(item)

    def _handle_choice(self, liked: bool) -> None:
        item = self._current_item()
        if item is None:
            return
        self.swiped.emit(item, liked)
        self.index += 1
        if self.index >= len(self.items):
            self._render()
            self.finished.emit()
        else:
            self._render()
