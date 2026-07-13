import sys

from PySide6.QtWidgets import QApplication

from app.config import DARK_TOKENS, LIGHT_TOKENS
from app.main_window import MainWindow
from app.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Watch Picker")

    window = MainWindow()

    def on_theme_changed(dark: bool) -> None:
        apply_theme(app, DARK_TOKENS if dark else LIGHT_TOKENS)

    window.state.theme_changed.connect(on_theme_changed)
    apply_theme(app, DARK_TOKENS if window.state.dark_mode else LIGHT_TOKENS)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
