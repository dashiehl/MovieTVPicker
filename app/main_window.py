from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.pages.discover_page import DiscoverPage
from app.pages.search_page import SearchPage
from app.pages.settings_page import SettingsPage
from app.pages.watched_page import WatchedPage
from app.pages.watchlist_page import WatchlistPage
from app.state import AppState
from app.widgets.banner import Banner
from app.widgets.freshness_note import FreshnessNote
from app.widgets.nav_bar import NavBar

PAGES = ["Discover", "Search", "Watchlist", "Watched", "Settings"]


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

        self.discover_page = DiscoverPage(self.catalog, self.image_loader, self.library, self.state)
        self.search_page = SearchPage(self.catalog, self.image_loader, self.library)
        self.watchlist_page = WatchlistPage(self.image_loader, self.library)
        self.watched_page = WatchedPage(self.image_loader, self.library)
        self.settings_page = SettingsPage(self.catalog)

        self._pages = {
            "Discover": self.discover_page,
            "Search": self.search_page,
            "Watchlist": self.watchlist_page,
            "Watched": self.watched_page,
            "Settings": self.settings_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)

        self.nav_bar.page_changed.connect(lambda name: self.nav_bar.set_active_page(name))

    def _go_to_page(self, name: str) -> None:
        self.stack.setCurrentWidget(self._pages[name])
