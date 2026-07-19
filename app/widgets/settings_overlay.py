from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from app.catalog_store import CatalogStore
from app.config import CATALOG_PATH, CATALOG_SEED_PATH, FONT_OPTIONS
from app.state import AppState
from app.widgets.mode_toggle import ModeToggle
from scripts.build_catalog import build_catalog


class CatalogBuildWorker(QObject):
    progress = Signal(str)
    finished = Signal(bool, str)

    def run(self) -> None:
        try:
            build_catalog(progress_callback=self.progress.emit)
            self.finished.emit(True, "Done.")
        except Exception as exc:  # noqa: BLE001 — surface any failure to the UI
            self.finished.emit(False, f"Rebuild failed: {exc}")


class SettingsOverlay(QFrame):
    """A left-docked panel (not a stacked page) — MainWindow keeps it pinned to
    the left 20% of the window and shows/hides it instead of navigating away."""

    def __init__(self, catalog: CatalogStore, state: AppState, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.state = state
        self._thread: QThread | None = None
        self._worker: CatalogBuildWorker | None = None

        self.setProperty("class", "overlay-panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setProperty("role", "h1")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setProperty("class", "nav-link")
        close_btn.setToolTip("Close settings")
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        appearance_label = QLabel("Appearance")
        appearance_label.setProperty("role", "h2")
        layout.addWidget(appearance_label)

        self.theme_btn = QPushButton("☀ Light mode" if self.state.dark_mode else "🌙 Dark mode")
        self.theme_btn.setProperty("class", "btn-secondary")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        font_label = QLabel("Font")
        font_label.setProperty("role", "muted")
        layout.addWidget(font_label)

        self.font_combo = QComboBox()
        for label, _stack in FONT_OPTIONS:
            self.font_combo.addItem(label)
        self.font_combo.setCurrentText(self.state.font_family)
        self.font_combo.currentTextChanged.connect(self.state.set_font_family)
        layout.addWidget(self.font_combo)

        who_label = QLabel("Who's watching")
        who_label.setProperty("role", "h2")
        layout.addWidget(who_label)
        layout.addWidget(ModeToggle(self.state))

        catalog_label = QLabel("Catalog")
        catalog_label.setProperty("role", "h2")
        layout.addWidget(catalog_label)

        self.info_label = QLabel()
        self.info_label.setProperty("role", "muted")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.rebuild_btn = QPushButton("Rebuild catalog now")
        self.rebuild_btn.setProperty("class", "btn")
        self.rebuild_btn.clicked.connect(self._start_rebuild)
        layout.addWidget(self.rebuild_btn)

        hint = QLabel(
            f"To add or remove titles, edit {CATALOG_SEED_PATH} and rebuild. "
            "A rebuild fetches one Wikipedia poster/blurb per title, so it can take a few minutes."
        )
        hint.setProperty("role", "muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        catalog.loaded.connect(self._refresh_info)
        self._refresh_info()

    def _toggle_theme(self) -> None:
        new_dark = not self.state.dark_mode
        self.state.set_dark_mode(new_dark)
        self.theme_btn.setText("☀ Light mode" if new_dark else "🌙 Dark mode")

    def _refresh_info(self) -> None:
        count = len(self.catalog.items)
        updated = self.catalog.updated_at or "never"
        self.info_label.setText(f"{count} titles · stored at {CATALOG_PATH} · last updated: {updated}")

    def _start_rebuild(self) -> None:
        self.rebuild_btn.setDisabled(True)
        self.log.clear()

        self._thread = QThread()
        self._worker = CatalogBuildWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.log.appendPlainText)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_finished(self, success: bool, message: str) -> None:
        self.rebuild_btn.setDisabled(False)
        self.log.appendPlainText(message)
        if success:
            self.catalog.load()
