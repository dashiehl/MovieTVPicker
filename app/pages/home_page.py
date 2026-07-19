from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.state import AppState
from app.theme import refresh_style

DECIDE_MODES = [
    ("Swipe", "Like or pass on picks, one at a time."),
    ("Mood Quiz", "Answer a few questions to get a match."),
    ("Browse", "Search, filter, and sort the whole catalog yourself."),
    ("Surprise", "Get one random pick, no questions asked."),
]


class HomePage(QWidget):
    start_requested = Signal(str)  # decide-mode name

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(28)
        layout.addStretch()

        who_title = QLabel("Who's watching today?")
        who_title.setProperty("role", "home-title")
        layout.addWidget(who_title)

        who_row = QHBoxLayout()
        who_row.setSpacing(16)
        self.solo_btn = QPushButton("Just me")
        self.solo_btn.setProperty("class", "choice-card")
        self.solo_btn.clicked.connect(lambda: self.state.set_mode("solo"))
        self.group_btn = QPushButton("Watching with friends")
        self.group_btn.setProperty("class", "choice-card")
        self.group_btn.clicked.connect(lambda: self.state.set_mode("group"))
        who_row.addWidget(self.solo_btn)
        who_row.addWidget(self.group_btn)
        layout.addLayout(who_row)

        decide_title = QLabel("How should we decide today?")
        decide_title.setProperty("role", "home-title")
        layout.addWidget(decide_title)

        decide_row = QHBoxLayout()
        decide_row.setSpacing(16)
        for name, blurb in DECIDE_MODES:
            btn = QPushButton(f"{name}\n{blurb}")
            btn.setProperty("class", "choice-card")
            btn.clicked.connect(lambda checked=False, n=name: self.start_requested.emit(n))
            decide_row.addWidget(btn)
        layout.addLayout(decide_row)

        layout.addStretch()

        self._refresh_who_buttons()
        self.state.mode_changed.connect(lambda _mode: self._refresh_who_buttons())

    def _refresh_who_buttons(self) -> None:
        self.solo_btn.setProperty("active", self.state.mode == "solo")
        self.group_btn.setProperty("active", self.state.mode == "group")
        refresh_style(self.solo_btn)
        refresh_style(self.group_btn)
