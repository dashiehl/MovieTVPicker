from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.utils import display_text
from app.widgets.movie_card import POSTER_SIZE

CARD_WIDTH = POSTER_SIZE[0] + 40  # must match MovieCard's setFixedWidth


class WatchedPage(QScrollArea):
    def __init__(self, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.image_loader = image_loader
        self.library = library
        self._cards: dict[str, QFrame] = {}
        self._ordered_cards: list[QFrame] = []
        self._columns = 0

        self.setWidgetResizable(True)

        library.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        items = sorted(self.library.watched, key=lambda i: i["watchedAt"], reverse=True)
        current_ids = {item["id"] for item in items}

        # Reuse existing card widgets for items that are still present — only
        # genuinely new/removed entries get built/destroyed — so the whole grid
        # doesn't flicker and re-fetch posters just because the count changed.
        for stale_id in [cid for cid in self._cards if cid not in current_ids]:
            card = self._cards.pop(stale_id)
            card.setParent(None)
            card.deleteLater()

        for item in items:
            if item["id"] not in self._cards:
                self._cards[item["id"]] = self._build_card(item)

        self._ordered_cards = [self._cards[item["id"]] for item in items]
        self._columns = max(1, self.viewport().width() // (CARD_WIDTH + 16))
        self._rebuild()

    def _rebuild(self) -> None:
        # QGridLayout keeps stale column-width metadata even after items are
        # taken out of it, so a changed column count needs a fresh layout
        # (and container) rather than reusing the old one. The card widgets
        # themselves are reused (reparented), not recreated.
        scroll_pos = self.verticalScrollBar().value()

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        if not self._ordered_cards:
            empty_label = QLabel("Nothing marked watched yet.")
            empty_label.setProperty("role", "empty-state")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setWordWrap(True)
            grid.addWidget(empty_label, 0, 0)
        else:
            columns = self._columns or 1
            for i, card in enumerate(self._ordered_cards):
                grid.addWidget(card, i // columns, i % columns)

        self.setWidget(container)
        self.verticalScrollBar().setValue(scroll_pos)

    def _reflow(self) -> None:
        if not self._cards:
            return
        columns = max(1, self.viewport().width() // (CARD_WIDTH + 16))
        if columns == self._columns:
            return
        self._columns = columns
        self._rebuild()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow()

    def _build_card(self, item: dict) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        card.setProperty("status", "watched")
        card.setFixedWidth(CARD_WIDTH)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(8)

        poster = QLabel("Loading…")
        poster.setFixedSize(*POSTER_SIZE)
        poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster.setWordWrap(True)
        layout.addWidget(poster, alignment=Qt.AlignmentFlag.AlignHCenter)

        def set_pixmap(pixmap):
            if pixmap is None:
                poster.setText(display_text(item["title"]))
                return
            poster.setPixmap(pixmap.scaled(*POSTER_SIZE, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            Qt.TransformationMode.SmoothTransformation))

        self.image_loader.load(item.get("posterPath"), set_pixmap)

        title = QLabel(display_text(item["title"]))
        title.setProperty("role", "h2")
        title.setWordWrap(True)
        title.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(title)

        watched_date = datetime.fromisoformat(item["watchedAt"].replace("Z", "+00:00")).strftime("%m/%d/%Y")
        meta = QLabel(f"Watched {watched_date}")
        meta.setProperty("role", "muted")
        meta.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(meta)

        actions = QHBoxLayout()
        actions.setContentsMargins(12, 4, 12, 0)
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("class", "card-action")
        remove_btn.clicked.connect(lambda: self.library.remove_from_watched(item["id"]))
        actions.addWidget(remove_btn)
        layout.addLayout(actions)

        return card
