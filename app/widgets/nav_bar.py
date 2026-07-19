from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app.state import AppState
from app.theme import refresh_style

# One flat nav row. "page" items route through the plain page stack; "mode" items
# route through the decide-mode stack — NavBar hides that distinction from callers,
# who just get a single active button and two signals to listen to.
NAV_ITEMS = [
    ("Home", "page"),
    ("Swipe", "mode"),
    ("Mood Quiz", "mode"),
    ("Browse", "mode"),
    ("Surprise", "mode"),
    ("Watchlist", "page"),
    ("Watched", "page"),
]


class NavBar(QFrame):
    page_changed = Signal(str)
    decide_mode_changed = Signal(str)

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

        self._nav_buttons: dict[str, QPushButton] = {}
        self._nav_kind: dict[str, str] = {}
        for name, kind in NAV_ITEMS:
            btn = QPushButton(name)
            btn.setProperty("class", "nav-link")
            btn.clicked.connect(lambda checked=False, n=name, k=kind: self._on_nav_clicked(n, k))
            layout.addWidget(btn)
            self._nav_buttons[name] = btn
            self._nav_kind[name] = kind
        self.set_active("Home")

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

    def _on_nav_clicked(self, name: str, kind: str) -> None:
        if kind == "page":
            self.page_changed.emit(name)
        else:
            self.decide_mode_changed.emit(name)

    def set_active(self, name: str) -> None:
        for n, btn in self._nav_buttons.items():
            btn.setProperty("active", n == name)
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
