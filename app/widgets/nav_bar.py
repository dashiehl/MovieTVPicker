from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app.state import AppState
from app.theme import refresh_style

PAGES = ["Discover", "Search", "Watchlist", "Watched", "Settings"]


class NavBar(QFrame):
    page_changed = Signal(str)

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.setObjectName("navBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)

        title = QLabel("🎬 Watch Picker")
        title.setProperty("role", "h1")
        layout.addWidget(title)
        layout.addStretch()

        self._page_buttons: dict[str, QPushButton] = {}
        for page in PAGES:
            btn = QPushButton(page)
            btn.setProperty("class", "nav-link")
            btn.clicked.connect(lambda checked=False, p=page: self.page_changed.emit(p))
            layout.addWidget(btn)
            self._page_buttons[page] = btn
        self.set_active_page("Discover")

        layout.addStretch()

        self.solo_btn = QPushButton("Solo")
        self.solo_btn.setProperty("class", "mode-toggle")
        self.solo_btn.clicked.connect(lambda: self.state.set_mode("solo"))
        self.group_btn = QPushButton("Group")
        self.group_btn.setProperty("class", "mode-toggle")
        self.group_btn.clicked.connect(lambda: self.state.set_mode("group"))
        layout.addWidget(self.solo_btn)
        layout.addWidget(self.group_btn)

        self.theme_btn = QPushButton("☀ Light" if self.state.dark_mode else "🌙 Dark")
        self.theme_btn.setProperty("class", "nav-link")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        self._refresh_mode_buttons()
        self.state.mode_changed.connect(lambda _mode: self._refresh_mode_buttons())

    def set_active_page(self, page: str) -> None:
        for name, btn in self._page_buttons.items():
            btn.setProperty("active", name == page)
            refresh_style(btn)

    def _refresh_mode_buttons(self) -> None:
        self.solo_btn.setProperty("active", self.state.mode == "solo")
        self.group_btn.setProperty("active", self.state.mode == "group")
        refresh_style(self.solo_btn)
        refresh_style(self.group_btn)

    def _toggle_theme(self) -> None:
        new_dark = not self.state.dark_mode
        self.state.set_dark_mode(new_dark)
        self.theme_btn.setText("☀ Light" if new_dark else "🌙 Dark")
