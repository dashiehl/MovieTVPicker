from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QStatusBar, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.pages.browse_mode import BrowseMode
from app.pages.group_swipe_mode import GroupSwipeMode
from app.pages.home_page import HomePage
from app.pages.mood_quiz_mode import MoodQuizMode
from app.pages.search_page import SearchPage
from app.pages.settings_page import SettingsPage
from app.pages.surprise_mode import SurpriseMode
from app.pages.swipe_mode import SwipeMode
from app.pages.watched_page import WatchedPage
from app.pages.watchlist_page import WatchlistPage
from app.state import AppState
from app.widgets.banner import Banner
from app.widgets.freshness_note import FreshnessNote
from app.widgets.nav_bar import NavBar

DECIDE_MODES = ["Swipe", "Mood Quiz", "Browse", "Surprise"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watch Picker")
        self.resize(1180, 800)

        self.state = AppState()
        self.catalog = CatalogStore()
        self.library = LibraryStore()
        self.image_loader = ImageLoader()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
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

        self.mood_quiz = MoodQuizMode(self.catalog, self.image_loader, self.library)
        self.browse = BrowseMode(self.catalog, self.image_loader, self.library)
        self.surprise = SurpriseMode(self.catalog, self.image_loader, self.library)

        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(self.swipe_stack)
        self.mode_stack.addWidget(self.mood_quiz)
        self.mode_stack.addWidget(self.browse)
        self.mode_stack.addWidget(self.surprise)

        self.search_page = SearchPage(self.catalog, self.image_loader, self.library)
        self.watchlist_page = WatchlistPage(self.image_loader, self.library)
        self.watched_page = WatchedPage(self.image_loader, self.library)
        self.settings_page = SettingsPage(self.catalog)

        self._pages = {
            "Home": self.home_page,
            "Search": self.search_page,
            "Watchlist": self.watchlist_page,
            "Watched": self.watched_page,
            "Settings": self.settings_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)
        self.stack.addWidget(self.mode_stack)

        self.home_page.start_requested.connect(self._go_to_decide_mode)
        self.nav_bar.decide_mode_changed.connect(self._go_to_decide_mode)
        self.nav_bar.page_changed.connect(lambda name: self.nav_bar.set_active_page(name))

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        settings_btn = QPushButton("⚙")
        settings_btn.setProperty("class", "nav-link")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(lambda: self._go_to_page("Settings"))
        status_bar.addWidget(settings_btn)

        self._go_to_page("Home")

    def _go_to_page(self, name: str) -> None:
        self.nav_bar.set_active_page(name)
        self.nav_bar.set_active_mode("")
        self.stack.setCurrentWidget(self._pages[name])

    def _go_to_decide_mode(self, decide_mode: str) -> None:
        self.mode_stack.setCurrentIndex(DECIDE_MODES.index(decide_mode))
        self.stack.setCurrentWidget(self.mode_stack)
        self.nav_bar.set_active_page("")
        self.nav_bar.set_active_mode(decide_mode)

    def _on_app_mode_changed(self, mode: str) -> None:
        self.swipe_stack.setCurrentWidget(self.swipe_group if mode == "group" else self.swipe_solo)
