from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.theme import refresh_style
from app.utils import catalog_key, display_text

POSTER_SIZE = (200, 300)


class MovieCard(QFrame):
    def __init__(self, item: dict, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.item = item
        self.library = library

        self.setProperty("class", "card")
        self.setFixedWidth(POSTER_SIZE[0] + 40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(8)

        self.poster_label = QLabel("Loading…")
        self.poster_label.setFixedSize(*POSTER_SIZE)
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_label.setWordWrap(True)
        self.poster_label.setScaledContents(False)
        layout.addWidget(self.poster_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        title_label = QLabel(display_text(item["title"]))
        title_label.setProperty("role", "h2")
        title_label.setWordWrap(True)
        title_label.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(title_label)

        media_label = "TV" if item["mediaType"] == "tv" else "Movie"
        meta_label = QLabel(f"{item.get('year') or 'Unknown year'} · {media_label}")
        meta_label.setProperty("role", "muted")
        meta_label.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(meta_label)

        actions = QVBoxLayout()
        actions.setContentsMargins(12, 4, 12, 0)
        actions.setSpacing(6)
        self.watchlist_btn = QPushButton()
        self.watchlist_btn.setProperty("class", "card-action")
        self.watchlist_btn.clicked.connect(lambda: self.library.add_to_watchlist(self.item))
        self.watched_btn = QPushButton()
        self.watched_btn.setProperty("class", "card-action")
        self.watched_btn.clicked.connect(lambda: self.library.mark_watched(self.item))
        actions.addWidget(self.watchlist_btn)
        actions.addWidget(self.watched_btn)
        layout.addLayout(actions)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        image_loader.load(item.get("posterPath"), self._set_pixmap)
        self._refresh_status()
        self.library.changed.connect(self._refresh_status)

    def _set_pixmap(self, pixmap) -> None:
        if pixmap is None:
            self.poster_label.setText(display_text(self.item["title"]))
            return
        scaled = pixmap.scaled(
            *POSTER_SIZE, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
        )
        self.poster_label.setPixmap(scaled)

    def _refresh_status(self) -> None:
        key = catalog_key(self.item)
        in_watchlist = key in self.library.watchlist_keys
        is_watched = key in self.library.watched_keys

        self.watchlist_btn.setText("In watchlist" if in_watchlist else "+ Watchlist")
        self.watchlist_btn.setDisabled(in_watchlist)
        self.watched_btn.setText("Watched" if is_watched else "Mark watched")
        self.watched_btn.setDisabled(is_watched)

        status = "watched" if is_watched else ("watchlist" if in_watchlist else "none")
        if self.property("status") != status:
            self.setProperty("status", status)
            refresh_style(self)
