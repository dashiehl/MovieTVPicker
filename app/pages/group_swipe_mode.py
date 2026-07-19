from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from app import db
from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.swipe_batch import pick_swipe_batch
from app.state import AppState
from app.theme import refresh_style
from app.utils import catalog_key
from app.widgets.banner import Banner
from app.widgets.movie_grid import MovieGrid
from app.widgets.swipe_deck import SwipeDeck

MEDIA_FILTERS = [("All", "all"), ("Movies", "movie"), ("TV Shows", "tv")]


def _clear_layout(layout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        widget = child.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()
        elif child.layout():
            _clear_layout(child.layout())


class GroupSwipeMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, state: AppState, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.image_loader = image_loader
        self.library = library
        self.state = state

        self.batch: list[dict] = []
        self.participant_index = 0
        self.likes_by_participant: dict[str, list[str]] = {}
        self._deck: SwipeDeck | None = None
        self.media_filter = "all"

        outer = QVBoxLayout(self)
        self.stack = QStackedWidget()
        outer.addWidget(self.stack)

        # --- setup page ---
        self.setup_page = QWidget()
        page_layout = QVBoxLayout(self.setup_page)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        setup_card = QFrame()
        setup_card.setProperty("class", "card")
        setup_card.setFixedWidth(420)
        setup_layout = QVBoxLayout(setup_card)
        setup_layout.setContentsMargins(28, 28, 28, 28)
        setup_layout.setSpacing(14)

        title = QLabel("Add each person swiping this round, then start the shared batch.")
        title.setWordWrap(True)
        setup_layout.addWidget(title)

        input_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Participant name")
        self.name_input.returnPressed.connect(self._add_participant)
        add_btn = QPushButton("Add")
        add_btn.setProperty("class", "btn-secondary")
        add_btn.clicked.connect(self._add_participant)
        input_row.addWidget(self.name_input)
        input_row.addWidget(add_btn)
        setup_layout.addLayout(input_row)

        self.participant_list_layout = QVBoxLayout()
        setup_layout.addLayout(self.participant_list_layout)

        filter_label = QLabel("What should we swipe on?")
        filter_label.setProperty("role", "muted")
        setup_layout.addWidget(filter_label)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label, value in MEDIA_FILTERS:
            btn = QPushButton(label)
            btn.setProperty("class", "sub-nav")
            btn.clicked.connect(lambda checked=False, v=value: self._set_media_filter(v))
            filter_row.addWidget(btn)
            self._filter_buttons[value] = btn
        setup_layout.addLayout(filter_row)
        self._refresh_filter_buttons()

        self.error_banner = Banner("error")
        setup_layout.addWidget(self.error_banner)

        self.start_btn = QPushButton("Start swiping (0 people)")
        self.start_btn.setProperty("class", "btn")
        self.start_btn.clicked.connect(self._start_session)
        setup_layout.addWidget(self.start_btn)

        self.hint_label = QLabel("Add at least 2 people to start.")
        self.hint_label.setProperty("role", "muted")
        setup_layout.addWidget(self.hint_label)

        page_layout.addWidget(setup_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.stack.addWidget(self.setup_page)

        # --- swiping page ---
        self.swiping_page = QWidget()
        self._swiping_layout = QVBoxLayout(self.swiping_page)
        self._swiping_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.stack.addWidget(self.swiping_page)

        # --- results page ---
        self.results_page = QWidget()
        results_layout = QVBoxLayout(self.results_page)
        results_title = QLabel("Everyone liked...")
        results_title.setProperty("role", "h1")
        results_layout.addWidget(results_title)
        self.results_grid = MovieGrid(image_loader, library, empty_message="No overlap this round — try another batch!")
        results_layout.addWidget(self.results_grid)
        again_btn = QPushButton("Swipe another batch")
        again_btn.setProperty("class", "btn")
        again_btn.clicked.connect(self._reset)
        results_layout.addWidget(again_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.stack.addWidget(self.results_page)

        self._refresh_setup_ui()

    def _add_participant(self) -> None:
        name = self.name_input.text().strip()
        if not name or name in self.state.group_participants:
            return
        self.state.set_group_participants([*self.state.group_participants, name])
        self.name_input.clear()
        self._refresh_setup_ui()

    def _remove_participant(self, name: str) -> None:
        self.state.set_group_participants([p for p in self.state.group_participants if p != name])
        self._refresh_setup_ui()

    def _set_media_filter(self, value: str) -> None:
        self.media_filter = value
        self._refresh_filter_buttons()

    def _refresh_filter_buttons(self) -> None:
        for value, btn in self._filter_buttons.items():
            btn.setProperty("active", value == self.media_filter)
            refresh_style(btn)

    def _refresh_setup_ui(self) -> None:
        _clear_layout(self.participant_list_layout)
        for name in self.state.group_participants:
            row = QHBoxLayout()
            row.addWidget(QLabel(name))
            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("class", "card-action")
            remove_btn.clicked.connect(lambda checked=False, n=name: self._remove_participant(n))
            row.addWidget(remove_btn)
            row.addStretch()
            self.participant_list_layout.addLayout(row)

        count = len(self.state.group_participants)
        self.start_btn.setText(f"Start swiping ({count} people)")
        self.start_btn.setDisabled(count < 2)
        self.hint_label.setVisible(count < 2)
        self.error_banner.set_text("")

    def _start_session(self) -> None:
        for name in self.state.group_participants:
            db.create_profile(name)

        self.batch = pick_swipe_batch(
            self.catalog.items, self.library.watched_keys, size=12, media_type=self.media_filter
        )
        if not self.batch:
            self.error_banner.set_text("No candidates available right now — try again later.")
            return

        self.likes_by_participant = {}
        self.participant_index = 0
        self.stack.setCurrentWidget(self.swiping_page)
        self._show_deck_for_current_participant()

    def _show_deck_for_current_participant(self) -> None:
        if self._deck is not None:
            self._swiping_layout.removeWidget(self._deck)
            self._deck.deleteLater()
        self._deck = SwipeDeck(self.batch, self.image_loader, self.library)
        self._deck.set_participant_label(self.state.group_participants[self.participant_index])
        self._deck.swiped.connect(self._on_swipe)
        self._deck.finished.connect(self._on_participant_finished)
        self._swiping_layout.addWidget(self._deck)

    def _on_swipe(self, item: dict, liked: bool) -> None:
        participant = self.state.group_participants[self.participant_index]
        db.record_swipe(item["id"], item["mediaType"], participant, liked)
        if liked:
            self.likes_by_participant.setdefault(participant, []).append(catalog_key(item))

    def _on_participant_finished(self) -> None:
        if self.participant_index + 1 < len(self.state.group_participants):
            self.participant_index += 1
            self._show_deck_for_current_participant()
        else:
            self._show_results()

    def _show_results(self) -> None:
        liked_sets = [set(self.likes_by_participant.get(name, [])) for name in self.state.group_participants]
        overlap = [item for item in self.batch if all(catalog_key(item) in s for s in liked_sets)]
        self.results_grid.set_items(overlap)
        self.stack.setCurrentWidget(self.results_page)

    def _reset(self) -> None:
        self.batch = []
        self.stack.setCurrentWidget(self.setup_page)
        self._refresh_setup_ui()
