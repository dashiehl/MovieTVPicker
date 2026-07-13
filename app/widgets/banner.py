from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from app.theme import refresh_style


class Banner(QFrame):
    """A warning/error banner frame — QSS targets QFrame[class="banner-warning"|"banner-error"]."""

    def __init__(self, kind: str = "warning", text: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._label = QLabel(text)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)
        self.set_kind(kind)
        self.hide() if not text else self.show()

    def set_kind(self, kind: str) -> None:
        self.setProperty("class", f"banner-{kind}")
        refresh_style(self)

    def set_text(self, text: str) -> None:
        self._label.setText(text)
        self.setVisible(bool(text))
