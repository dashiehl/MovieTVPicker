import sys

from PySide6.QtWidgets import QApplication

from app.config import DARK_TOKENS, LIGHT_TOKENS
from app.main_window import MainWindow
from app.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Watch Picker")

    window = MainWindow()

    def refresh_theme(*_args) -> None:
        tokens = DARK_TOKENS if window.state.dark_mode else LIGHT_TOKENS
        apply_theme(app, tokens, window.state.font_family)

    window.state.theme_changed.connect(refresh_theme)
    window.state.font_changed.connect(refresh_theme)
    refresh_theme()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
