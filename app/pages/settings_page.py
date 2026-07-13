from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.config import CATALOG_PATH, CATALOG_SEED_PATH
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


class SettingsPage(QWidget):
    def __init__(self, catalog: CatalogStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self._thread: QThread | None = None
        self._worker: CatalogBuildWorker | None = None

        layout = QVBoxLayout(self)

        title = QLabel("Catalog")
        title.setProperty("role", "h1")
        layout.addWidget(title)

        self.info_label = QLabel()
        self.info_label.setProperty("role", "muted")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.rebuild_btn = QPushButton("Rebuild catalog now")
        self.rebuild_btn.setProperty("class", "btn")
        self.rebuild_btn.setFixedWidth(220)
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
