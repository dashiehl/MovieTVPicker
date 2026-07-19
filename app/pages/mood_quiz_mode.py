from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QPushButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.mood_quiz import FAMILIARITY_OPTIONS, TONE_GENRES, resolve_quiz
from app.theme import refresh_style
from app.widgets.movie_grid import MovieGrid

QUESTIONS = [
    {"key": "mediaType", "prompt": "What are you in the mood for?", "labels": {"movie": "A movie", "tv": "A TV show"}},
    {"key": "genre", "prompt": "What genre(s) sound good?"},
    {"key": "tone", "prompt": "What tone(s) are you after?", "options": list(TONE_GENRES.keys())},
    {"key": "familiarity", "prompt": "Older classics or something recent?", "options": FAMILIARITY_OPTIONS},
]

DEFAULT_COUNT = 5

MIN_CARD_WIDTH = 480
MAX_CARD_WIDTH = 920
CARD_MARGIN = 32  # each side, matches _question_layout's contentsMargins
BUTTON_MIN_WIDTH = 150
GRID_SPACING = 10


def _clear_layout(layout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        widget = child.widget()
        if widget:
            # setParent(None) detaches immediately; deleteLater() alone leaves the
            # widget alive (and findable/clickable) until the event loop next spins,
            # which matters here since every step reuses the same "Continue" label.
            widget.setParent(None)
            widget.deleteLater()
        elif child.layout():
            _clear_layout(child.layout())


class MoodQuizMode(QWidget):
    def __init__(self, catalog: CatalogStore, image_loader: ImageLoader, library: LibraryStore, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.image_loader = image_loader
        self.library = library
        self.step = 0
        self.answers: dict = {}
        self._selection: set[str] = set()
        self._continue_btn: QPushButton | None = None
        self._count = DEFAULT_COUNT
        self.count_spin: QSpinBox | None = None
        self._current_question: dict | None = None  # non-None only while a multi-select question is showing
        self._current_columns = 0

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.question_page = QWidget()
        page_layout = QVBoxLayout(self.question_page)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.question_card = QFrame()
        self.question_card.setProperty("class", "card")
        self.question_card.setFixedWidth(MIN_CARD_WIDTH)
        self._question_layout = QVBoxLayout(self.question_card)
        self._question_layout.setContentsMargins(CARD_MARGIN, CARD_MARGIN, CARD_MARGIN, CARD_MARGIN)
        self._question_layout.setSpacing(20)
        self._question_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        page_layout.addWidget(self.question_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.stack.addWidget(self.question_page)

        self.result_page = QWidget()
        result_layout = QVBoxLayout(self.result_page)
        result_layout.setSpacing(16)

        self.results_title = QLabel("Your picks")
        self.results_title.setProperty("role", "h1")
        result_layout.addWidget(self.results_title, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.results_grid = MovieGrid(
            image_loader, library,
            empty_message="Couldn't find any matches for that combo — try different answers.",
        )
        result_layout.addWidget(self.results_grid)

        restart_btn = QPushButton("Start over")
        restart_btn.setProperty("class", "btn")
        restart_btn.clicked.connect(self._restart)
        result_layout.addWidget(restart_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.stack.addWidget(self.result_page)

        self._render_step()

    def _current_options(self, question: dict) -> list[str]:
        if question["key"] == "mediaType":
            return ["movie", "tv"]
        if question["key"] == "genre":
            media_types = set(self.answers.get("mediaType") or ["movie", "tv"])
            genres = {
                g for item in self.catalog.items if item["mediaType"] in media_types for g in item["genres"]
            }
            return sorted(genres)
        return question["options"]

    def _fit_card_width(self) -> int:
        available = self.width() - 80 if self.width() > 0 else MAX_CARD_WIDTH
        return max(MIN_CARD_WIDTH, min(MAX_CARD_WIDTH, available))

    def _fit_columns(self, card_width: int, option_count: int) -> int:
        inner = card_width - 2 * CARD_MARGIN
        by_width = max(1, (inner + GRID_SPACING) // (BUTTON_MIN_WIDTH + GRID_SPACING))
        return max(1, min(by_width, option_count))

    def _render_step(self) -> None:
        question = QUESTIONS[self.step]
        self._selection = set(self.answers.get(question["key"], []))
        self._current_question = question
        self._build_question_layout()

    def _build_question_layout(self) -> None:
        question = self._current_question
        self.stack.setCurrentWidget(self.question_page)
        _clear_layout(self._question_layout)

        progress = QLabel(f"Step {self.step + 1} of {len(QUESTIONS) + 1}")
        progress.setProperty("role", "muted")
        progress.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._question_layout.addWidget(progress)

        prompt = QLabel(question["prompt"])
        prompt.setProperty("role", "h1")
        prompt.setWordWrap(True)
        prompt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._question_layout.addWidget(prompt)

        hint = QLabel("Pick one or more, then continue.")
        hint.setProperty("role", "muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._question_layout.addWidget(hint)

        options = self._current_options(question)
        card_width = self._fit_card_width()
        columns = self._fit_columns(card_width, len(options))
        self._current_columns = columns
        self.question_card.setFixedWidth(card_width)

        options_grid = QGridLayout()
        options_grid.setSpacing(GRID_SPACING)
        for i, opt in enumerate(options):
            label = question.get("labels", {}).get(opt, opt)
            btn = QPushButton(label)
            btn.setProperty("class", "sub-nav")
            btn.setMinimumHeight(40)
            btn.setCheckable(True)
            btn.setChecked(opt in self._selection)
            btn.setProperty("active", opt in self._selection)
            btn.toggled.connect(lambda checked, v=opt, b=btn: self._toggle_option(v, checked, b))
            options_grid.addWidget(btn, i // columns, i % columns)
        self._question_layout.addLayout(options_grid)

        self._continue_btn = QPushButton("Continue")
        self._continue_btn.setProperty("class", "btn")
        self._continue_btn.setDisabled(not self._selection)
        self._continue_btn.clicked.connect(lambda: self._answer(question, sorted(self._selection)))
        self._question_layout.addWidget(self._continue_btn)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._current_question is None:
            return
        card_width = self._fit_card_width()
        columns = self._fit_columns(card_width, len(self._current_options(self._current_question)))
        if columns != self._current_columns:
            self._build_question_layout()

    def _toggle_option(self, value: str, checked: bool, btn: QPushButton) -> None:
        if checked:
            self._selection.add(value)
        else:
            self._selection.discard(value)
        btn.setProperty("active", checked)
        refresh_style(btn)
        if self._continue_btn is not None:
            self._continue_btn.setDisabled(not self._selection)

    def _answer(self, question: dict, value: list[str]) -> None:
        self.answers[question["key"]] = value
        if self.step + 1 < len(QUESTIONS):
            self.step += 1
            self._render_step()
        else:
            self._render_count_step()

    def _render_count_step(self) -> None:
        self._current_question = None
        self.stack.setCurrentWidget(self.question_page)
        _clear_layout(self._question_layout)
        self.question_card.setFixedWidth(MIN_CARD_WIDTH)

        progress = QLabel(f"Step {len(QUESTIONS) + 1} of {len(QUESTIONS) + 1}")
        progress.setProperty("role", "muted")
        progress.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._question_layout.addWidget(progress)

        prompt = QLabel("How many suggestions do you want?")
        prompt.setProperty("role", "h1")
        prompt.setWordWrap(True)
        prompt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._question_layout.addWidget(prompt)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(self._count)
        self.count_spin.setFixedWidth(100)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._question_layout.addWidget(self.count_spin, alignment=Qt.AlignmentFlag.AlignHCenter)

        see_btn = QPushButton("See picks")
        see_btn.setProperty("class", "btn")
        see_btn.clicked.connect(self._run_quiz)
        self._question_layout.addWidget(see_btn)

    def _run_quiz(self) -> None:
        self._count = self.count_spin.value() if self.count_spin else DEFAULT_COUNT
        results = resolve_quiz(self.catalog.items, self.answers, self._count)
        self.results_title.setText(f"Your picks ({len(results)})" if results else "Your picks")
        self.results_grid.set_items(results)
        self.stack.setCurrentWidget(self.result_page)

    def _restart(self) -> None:
        self.step = 0
        self.answers = {}
        self._selection = set()
        self._count = DEFAULT_COUNT
        self._render_step()
