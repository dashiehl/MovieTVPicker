from datetime import datetime, timezone

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.config import STALE_AFTER_DAYS
from app.theme import refresh_style


class FreshnessNote(QWidget):
    def __init__(self, catalog: CatalogStore, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 12)

        self._banner = QFrame()
        banner_layout = QVBoxLayout(self._banner)
        self._label = QLabel()
        self._label.setWordWrap(True)
        banner_layout.addWidget(self._label)
        outer.addWidget(self._banner)

        self._catalog = catalog
        catalog.loaded.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self._render(self._catalog.updated_at)

    def _render(self, updated_at: str | None) -> None:
        if not updated_at:
            self.hide()
            return
        self.show()
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - parsed).days
        date_label = parsed.strftime("%m/%d/%Y")

        if age_days > STALE_AFTER_DAYS:
            self._banner.setProperty("class", "banner-warning")
            self._label.setProperty("role", "")
            self._label.setText(
                f"Catalog last updated {date_label} — it's been a while. "
                "Use Settings → Rebuild catalog to refresh titles and posters."
            )
        else:
            self._banner.setProperty("class", "")
            self._label.setProperty("role", "muted")
            self._label.setText(f"Catalog last updated: {date_label}")

        refresh_style(self._banner)
        refresh_style(self._label)
