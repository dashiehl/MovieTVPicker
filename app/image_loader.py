"""Async poster image loading with a persistent on-disk cache.

Uses QNetworkAccessManager so loads never block the UI thread. Cached
images live in data/image_cache/, keyed by a hash of the source URL, so
posters only need to be downloaded once per machine.
"""

import hashlib
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from app.config import IMAGE_CACHE_DIR


class ImageLoader(QObject):
    def __init__(self):
        super().__init__()
        self._manager = QNetworkAccessManager(self)
        self._pending: dict[str, list[Callable[[Optional[QPixmap]], None]]] = {}
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return IMAGE_CACHE_DIR / f"{digest}.img"

    def load(self, url: Optional[str], callback: Callable[[Optional[QPixmap]], None]) -> None:
        if not url:
            callback(None)
            return

        cache_path = self._cache_path(url)
        if cache_path.exists():
            pixmap = QPixmap()
            if pixmap.loadFromData(cache_path.read_bytes()):
                callback(pixmap)
                return

        if url in self._pending:
            self._pending[url].append(callback)
            return
        self._pending[url] = [callback]

        reply = self._manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_finished(url, reply, cache_path))

    def _on_finished(self, url: str, reply: QNetworkReply, cache_path: Path) -> None:
        callbacks = self._pending.pop(url, [])
        data = reply.readAll()
        reply.deleteLater()

        pixmap = QPixmap()
        if reply.error() == QNetworkReply.NetworkError.NoError and pixmap.loadFromData(data):
            try:
                cache_path.write_bytes(bytes(data))
            except OSError:
                pass
            for cb in callbacks:
                cb(pixmap)
        else:
            for cb in callbacks:
                cb(None)
