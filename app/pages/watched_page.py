from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.image_loader import ImageLoader
from app.library_store import LibraryStore

CARD_WIDTH = 184
POSTER_SIZE = (160, 240)


class WatchedPage(QScrollArea):
    def __init__(self, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.image_loader = image_loader
        self.library = library

        self.setWidgetResizable(True)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        library.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = sorted(self.library.watched, key=lambda i: i["watchedAt"], reverse=True)
        if not items:
            empty_label = QLabel("Nothing marked watched yet.")
            empty_label.setProperty("role", "empty-state")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(empty_label, 0, 0)
            return

        columns = max(1, (self.viewport().width() or 900) // (CARD_WIDTH + 16))
        for i, item in enumerate(items):
            card = self._build_card(item)
            self._grid.addWidget(card, i // columns, i % columns)

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
                poster.setText(item["title"])
                return
            poster.setPixmap(pixmap.scaled(*POSTER_SIZE, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            Qt.TransformationMode.SmoothTransformation))

        self.image_loader.load(item.get("posterPath"), set_pixmap)

        title = QLabel(item["title"])
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
