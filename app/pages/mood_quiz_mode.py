from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.catalog_store import CatalogStore
from app.image_loader import ImageLoader
from app.library_store import LibraryStore
from app.logic.mood_quiz import FAMILIARITY_OPTIONS, TONE_GENRES, resolve_quiz
from app.widgets.movie_card import MovieCard

QUESTIONS = [
    {"key": "mediaType", "prompt": "What are you in the mood for?", "labels": {"movie": "A movie", "tv": "A TV show"}},
    {"key": "genre", "prompt": "What genre sounds good?"},
    {"key": "tone", "prompt": "What tone are you after?", "options": list(TONE_GENRES.keys())},
    {"key": "familiarity", "prompt": "Older classic or something recent?", "options": FAMILIARITY_OPTIONS},
]


def _clear_layout(layout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
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
        self._result_card: MovieCard | None = None

        outer = QVBoxLayout(self)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack)

        self.question_page = QWidget()
        self._question_layout = QVBoxLayout(self.question_page)
        self._question_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stack.addWidget(self.question_page)

        self.result_page = QWidget()
        self._result_layout = QVBoxLayout(self.result_page)
        self._result_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.stack.addWidget(self.result_page)

        self._render_step()

    def _current_options(self, question: dict) -> list[str]:
        if question["key"] == "mediaType":
            return ["movie", "tv"]
        if question["key"] == "genre":
            media_type = self.answers.get("mediaType", "movie")
            genres = {g for item in self.catalog.items if item["mediaType"] == media_type for g in item["genres"]}
            return sorted(genres)
        return question["options"]

    def _render_step(self) -> None:
        self.stack.setCurrentWidget(self.question_page)
        _clear_layout(self._question_layout)

        question = QUESTIONS[self.step]
        prompt = QLabel(question["prompt"])
        prompt.setProperty("role", "h1")
        self._question_layout.addWidget(prompt)

        options_row = QHBoxLayout()
        for opt in self._current_options(question):
            label = question.get("labels", {}).get(opt, opt)
            btn = QPushButton(label)
            btn.setProperty("class", "sub-nav")
            btn.clicked.connect(lambda checked=False, q=question, v=opt: self._answer(q, v))
            options_row.addWidget(btn)
        options_row.addStretch()
        self._question_layout.addLayout(options_row)

    def _answer(self, question: dict, value: str) -> None:
        self.answers[question["key"]] = value
        if self.step + 1 < len(QUESTIONS):
            self.step += 1
            self._render_step()
        else:
            self._run_quiz()

    def _run_quiz(self) -> None:
        result = resolve_quiz(self.catalog.items, self.answers)
        self.stack.setCurrentWidget(self.result_page)
        _clear_layout(self._result_layout)

        if result:
            self._result_card = MovieCard(result, self.image_loader, self.library)
            self._result_layout.addWidget(self._result_card, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            empty = QLabel("Couldn't find a match for that combo — try different answers.")
            empty.setProperty("role", "empty-state")
            self._result_layout.addWidget(empty)

        restart_btn = QPushButton("Start over")
        restart_btn.setProperty("class", "btn")
        restart_btn.clicked.connect(self._restart)
        self._result_layout.addWidget(restart_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _restart(self) -> None:
        self.step = 0
        self.answers = {}
        self._render_step()
