from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal

from .quotes import hourly_text
from .storage import ReminderStore


HOURLY_REPEAT_COUNT = 3
HOURLY_REPEAT_INTERVAL_SECONDS = 10


class ReminderScheduler(QObject):
    fly_requested = Signal(str)
    data_changed = Signal()

    def __init__(self, store: ReminderStore):
        super().__init__()
        self.store = store
        self.hourly_enabled = True
        self._last_check = datetime.now().replace(microsecond=0)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._last_check = datetime.now().replace(microsecond=0)
        self._timer.start()

    def set_hourly_enabled(self, enabled: bool) -> None:
        self.hourly_enabled = enabled

    def _tick(self) -> None:
        now = datetime.now().replace(microsecond=0)
        gap = now - self._last_check

        # Sleep, hibernation, or a blocked event loop should not replay old alerts.
        if gap > timedelta(seconds=60):
            self._last_check = now
            self._skip_missed_meeting_attempts(now)
            return

        if self.hourly_enabled:
            self._check_hourly(now)

        changed = self._check_meetings(now)
        if changed:
            self.store.persist_runtime_changes()
            self.data_changed.emit()

        self._last_check = now

    def _check_hourly(self, now: datetime) -> None:
        if not (8 <= now.hour <= 23):
            return

        top_of_hour = now.replace(minute=0, second=0, microsecond=0)
        grace = timedelta(seconds=3)
        for index in range(HOURLY_REPEAT_COUNT):
            fire_time = top_of_hour + timedelta(
                seconds=index * HOURLY_REPEAT_INTERVAL_SECONDS
            )
            if self._last_check < fire_time <= now and now - fire_time <= grace:
                self.fly_requested.emit(hourly_text(now.hour, index))
                break

    def _check_meetings(self, now: datetime) -> bool:
        changed = False
        grace = timedelta(seconds=3)

        for reminder in self.store.all():
            if reminder.completed:
                continue

            while reminder.next_fire_index < 3:
                fire_time = reminder.fire_time_for_index(reminder.next_fire_index)
                if fire_time > now:
                    break

                if self._last_check < fire_time <= now and now - fire_time <= grace:
                    reminder.reminded_count += 1
                    reminder.next_fire_index += 1
                    reminder.last_reminded_at = now
                    changed = True
                    self.fly_requested.emit(
                        f"{reminder.meeting_at:%H:%M} {reminder.text} 3分钟后开始"
                    )
                    break

                # This attempt is already in the past, so keep the record but do
                # not replay it.
                reminder.next_fire_index += 1
                changed = True

            if reminder.next_fire_index >= 3 or now >= reminder.meeting_at:
                if not reminder.completed:
                    reminder.completed = True
                    changed = True

        return changed

    def _skip_missed_meeting_attempts(self, now: datetime) -> None:
        changed = False
        for reminder in self.store.all():
            if reminder.completed:
                continue

            while reminder.next_fire_index < 3:
                fire_time = reminder.fire_time_for_index(reminder.next_fire_index)
                if fire_time > now:
                    break
                reminder.next_fire_index += 1
                changed = True

            if reminder.next_fire_index >= 3 or now >= reminder.meeting_at:
                reminder.completed = True
                changed = True

        if changed:
            self.store.persist_runtime_changes()
            self.data_changed.emit()
