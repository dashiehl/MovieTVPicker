from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.pages.browse_mode import BrowseMode
from app.pages.group_swipe_mode import GroupSwipeMode
from app.pages.mood_quiz_mode import MoodQuizMode
from app.pages.surprise_mode import SurpriseMode
from app.pages.swipe_mode import SwipeMode
from app.state import AppState
from app.theme import refresh_style

MODES = ["Swipe", "Mood Quiz", "Browse", "Surprise"]


class DiscoverPage(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)

        subnav = QHBoxLayout()
        self._buttons: dict[str, QPushButton] = {}
        for name in MODES:
            btn = QPushButton(name)
            btn.setProperty("class", "sub-nav")
            btn.clicked.connect(lambda checked=False, n=name: self._set_mode(n))
            subnav.addWidget(btn)
            self._buttons[name] = btn
        subnav.addStretch()
        layout.addLayout(subnav)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.swipe_solo = SwipeMode(catalog, image_loader, library, state)
        self.swipe_group = GroupSwipeMode(catalog, image_loader, library, state)
        self.swipe_stack = QStackedWidget()
        self.swipe_stack.addWidget(self.swipe_solo)
        self.swipe_stack.addWidget(self.swipe_group)
        self.stack.addWidget(self.swipe_stack)

        self.mood_quiz = MoodQuizMode(catalog, image_loader, library)
        self.stack.addWidget(self.mood_quiz)

        self.browse = BrowseMode(catalog, image_loader, library)
        self.stack.addWidget(self.browse)

        self.surprise = SurpriseMode(catalog, image_loader, library)
        self.stack.addWidget(self.surprise)

        state.mode_changed.connect(self._on_app_mode_changed)
        self._on_app_mode_changed(state.mode)
        self._set_mode("Swipe")

    def _on_app_mode_changed(self, mode: str) -> None:
        self.swipe_stack.setCurrentWidget(self.swipe_group if mode == "group" else self.swipe_solo)

    def _set_mode(self, name: str) -> None:
        for n, btn in self._buttons.items():
            btn.setProperty("active", n == name)
            refresh_style(btn)
        self.stack.setCurrentIndex(MODES.index(name))
