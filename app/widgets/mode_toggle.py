from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from app.state import AppState
from app.theme import refresh_style


class ModeToggle(QWidget):
    """Solo/Group pill toggle bound directly to AppState.mode — used wherever
    the current swipe party size needs to be picked (Swipe mode, Settings)."""

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.solo_btn = QPushButton("Solo")
        self.solo_btn.setProperty("class", "mode-toggle")
        self.solo_btn.clicked.connect(lambda: self.state.set_mode("solo"))
        self.group_btn = QPushButton("Group")
        self.group_btn.setProperty("class", "mode-toggle")
        self.group_btn.clicked.connect(lambda: self.state.set_mode("group"))
        layout.addWidget(self.solo_btn)
        layout.addWidget(self.group_btn)

        self._refresh()
        self.state.mode_changed.connect(lambda _mode: self._refresh())

    def _refresh(self) -> None:
        self.solo_btn.setProperty("active", self.state.mode == "solo")
        self.group_btn.setProperty("active", self.state.mode == "group")
        refresh_style(self.solo_btn)
        refresh_style(self.group_btn)
