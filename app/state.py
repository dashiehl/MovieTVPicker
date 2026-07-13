from PySide6.QtCore import QObject, Signal

from app.config import SOLO_PROFILE


class AppState(QObject):
    mode_changed = Signal(str)  # "solo" | "group"
    participants_changed = Signal(list)
    theme_changed = Signal(bool)  # dark_mode

    def __init__(self):
        super().__init__()
        self._mode = "solo"
        self._group_participants: list[str] = []
        self._dark_mode = True

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode != self._mode:
            self._mode = mode
            self.mode_changed.emit(mode)

    @property
    def is_group(self) -> bool:
        return self._mode == "group"

    @property
    def solo_profile(self) -> str:
        return SOLO_PROFILE

    @property
    def group_participants(self) -> list[str]:
        return self._group_participants

    def set_group_participants(self, participants: list[str]) -> None:
        self._group_participants = participants
        self.participants_changed.emit(participants)

    @property
    def dark_mode(self) -> bool:
        return self._dark_mode

    def set_dark_mode(self, dark: bool) -> None:
        if dark != self._dark_mode:
            self._dark_mode = dark
            self.theme_changed.emit(dark)
