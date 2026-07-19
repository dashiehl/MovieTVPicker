from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QStatusBar, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.pages.browse_mode import BrowseMode
from app.pages.group_swipe_mode import GroupSwipeMode
from app.pages.home_page import HomePage
from app.pages.mood_quiz_mode import MoodQuizMode
from app.pages.surprise_mode import SurpriseMode
from app.pages.swipe_mode import SwipeMode
from app.pages.watched_page import WatchedPage
from app.pages.watchlist_page import WatchlistPage
from app.state import AppState
from app.widgets.banner import Banner
from app.widgets.freshness_note import FreshnessNote
from app.widgets.mode_toggle import ModeToggle
from app.widgets.nav_bar import NavBar
from app.widgets.settings_overlay import SettingsOverlay

DECIDE_MODES = ["Swipe", "Mood Quiz", "Browse", "Surprise"]
SETTINGS_OVERLAY_WIDTH_FRACTION = 0.2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watch Picker")
        self.setMinimumSize(860, 600)
        self.resize(1180, 800)

        self.state = AppState()
        self.catalog = CatalogStore()
        self.library = LibraryStore()
        self.image_loader = ImageLoader()

        self.central = QWidget()
        self.setCentralWidget(self.central)
        layout = QVBoxLayout(self.central)
        layout.setContentsMargins(16, 8, 16, 16)

        self.nav_bar = NavBar(self.state)
        self.nav_bar.page_changed.connect(self._go_to_page)
        layout.addWidget(self.nav_bar)

        self.freshness_note = FreshnessNote(self.catalog)
        layout.addWidget(self.freshness_note)

        self.error_banner = Banner("error")
        layout.addWidget(self.error_banner)
        self.catalog.error.connect(self.error_banner.set_text)
        self.catalog.loaded.connect(lambda: self.error_banner.set_text(""))

        self.catalog.load()  # must happen before building pages, which read catalog.items synchronously

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.home_page = HomePage(self.state)

        self.swipe_solo = SwipeMode(self.catalog, self.image_loader, self.library, self.state)
        self.swipe_group = GroupSwipeMode(self.catalog, self.image_loader, self.library, self.state)
        self.swipe_stack = QStackedWidget()
        self.swipe_stack.addWidget(self.swipe_solo)
        self.swipe_stack.addWidget(self.swipe_group)
        self.state.mode_changed.connect(self._on_app_mode_changed)
        self._on_app_mode_changed(self.state.mode)

        # Solo/Group only matters for Swipe, so it lives here instead of the nav bar.
        swipe_page = QWidget()
        swipe_layout = QVBoxLayout(swipe_page)
        swipe_layout.setContentsMargins(0, 0, 0, 0)
        swipe_layout.setSpacing(8)
        swipe_layout.addWidget(ModeToggle(self.state), alignment=Qt.AlignmentFlag.AlignHCenter)
        swipe_layout.addWidget(self.swipe_stack)

        self.mood_quiz = MoodQuizMode(self.catalog, self.image_loader, self.library)
        self.browse = BrowseMode(self.catalog, self.image_loader, self.library)
        self.surprise = SurpriseMode(self.catalog, self.image_loader, self.library)

        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(swipe_page)
        self.mode_stack.addWidget(self.mood_quiz)
        self.mode_stack.addWidget(self.browse)
        self.mode_stack.addWidget(self.surprise)

        self.watchlist_page = WatchlistPage(self.image_loader, self.library)
        self.watched_page = WatchedPage(self.image_loader, self.library)

        self._pages = {
            "Home": self.home_page,
            "Watchlist": self.watchlist_page,
            "Watched": self.watched_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)
        self.stack.addWidget(self.mode_stack)

        self.home_page.start_requested.connect(self._go_to_decide_mode)
        self.nav_bar.decide_mode_changed.connect(self._go_to_decide_mode)

        self.settings_overlay = SettingsOverlay(self.catalog, self.state, parent=self.central)
        self.settings_overlay.hide()

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        settings_btn = QPushButton("⚙")
        settings_btn.setProperty("class", "nav-link")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._toggle_settings)
        status_bar.addWidget(settings_btn)

        self._go_to_page("Home")

    def _go_to_page(self, name: str) -> None:
        self.nav_bar.set_active(name)
        self.stack.setCurrentWidget(self._pages[name])

    def _go_to_decide_mode(self, decide_mode: str) -> None:
        self.mode_stack.setCurrentIndex(DECIDE_MODES.index(decide_mode))
        self.stack.setCurrentWidget(self.mode_stack)
        self.nav_bar.set_active(decide_mode)

    def _on_app_mode_changed(self, mode: str) -> None:
        self.swipe_stack.setCurrentWidget(self.swipe_group if mode == "group" else self.swipe_solo)

    def _toggle_settings(self) -> None:
        if self.settings_overlay.isVisible():
            self.settings_overlay.hide()
            return
        self._position_settings_overlay()
        self.settings_overlay.show()
        self.settings_overlay.raise_()

    def _position_settings_overlay(self) -> None:
        width = round(self.central.width() * SETTINGS_OVERLAY_WIDTH_FRACTION)
        self.settings_overlay.setGeometry(self.central.width() - width, 0, width, self.central.height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_settings_overlay()
