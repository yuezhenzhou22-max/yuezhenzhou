from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from .models import Reminder


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = app_root()
DEFAULT_DATA_FILE = PROJECT_ROOT / "reminders.json"


class ReminderStore(QObject):
    reminders_changed = Signal()

    def __init__(self, path: Path = DEFAULT_DATA_FILE):
        super().__init__()
        self.path = path
        self._reminders: list[Reminder] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._reminders = []
            return

        try:
            raw_items = json.loads(self.path.read_text(encoding="utf-8"))
            self._reminders = [Reminder.from_dict(item) for item in raw_items]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            backup = self.path.with_suffix(".broken.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            self._reminders = []

    def save(self, emit: bool = True) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        payload = [reminder.to_dict() for reminder in self._reminders]
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self.path)
        if emit:
            self.reminders_changed.emit()

    def all(self) -> list[Reminder]:
        return list(self._reminders)

    def find(self, reminder_id: str) -> Reminder | None:
        for reminder in self._reminders:
            if reminder.id == reminder_id:
                return reminder
        return None

    def add(self, reminder: Reminder) -> None:
        self._reminders.append(reminder)
        self.save()

    def update(self, reminder_id: str, meeting_at, text: str) -> bool:
        reminder = self.find(reminder_id)
        if reminder is None:
            return False

        reminder.meeting_at = meeting_at.replace(second=0, microsecond=0)
        reminder.text = text.strip()
        reminder.reset_schedule_state()
        self.save()
        return True

    def delete(self, reminder_id: str) -> bool:
        original_count = len(self._reminders)
        self._reminders = [
            reminder for reminder in self._reminders if reminder.id != reminder_id
        ]
        changed = len(self._reminders) != original_count
        if changed:
            self.save()
        return changed

    def persist_runtime_changes(self) -> None:
        self.save()
