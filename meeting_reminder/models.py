from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4


def clean_datetime(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat()


@dataclass
class Reminder:
    id: str
    meeting_at: datetime
    text: str
    created_at: datetime
    reminded_count: int = 0
    completed: bool = False
    next_fire_index: int = 0
    last_reminded_at: datetime | None = None

    @classmethod
    def create(cls, meeting_at: datetime, text: str) -> "Reminder":
        return cls(
            id=str(uuid4()),
            meeting_at=clean_datetime(meeting_at),
            text=text.strip(),
            created_at=datetime.now().replace(microsecond=0),
        )

    @classmethod
    def from_dict(cls, raw: dict) -> "Reminder":
        return cls(
            id=str(raw.get("id") or uuid4()),
            meeting_at=parse_datetime(raw["meeting_at"]),
            text=str(raw.get("text", "")).strip(),
            created_at=parse_datetime(raw.get("created_at") or datetime.now().isoformat()),
            reminded_count=int(raw.get("reminded_count", 0)),
            completed=bool(raw.get("completed", False)),
            next_fire_index=int(raw.get("next_fire_index", raw.get("reminded_count", 0))),
            last_reminded_at=(
                parse_datetime(raw["last_reminded_at"])
                if raw.get("last_reminded_at")
                else None
            ),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_at": to_iso(self.meeting_at),
            "text": self.text,
            "created_at": to_iso(self.created_at),
            "reminded_count": self.reminded_count,
            "completed": self.completed,
            "next_fire_index": self.next_fire_index,
            "last_reminded_at": to_iso(self.last_reminded_at),
        }

    @property
    def trigger_start(self) -> datetime:
        return self.meeting_at - timedelta(minutes=3)

    def fire_time_for_index(self, index: int) -> datetime:
        return self.trigger_start + timedelta(seconds=index * 10)

    def reset_schedule_state(self) -> None:
        self.reminded_count = 0
        self.completed = False
        self.next_fire_index = 0
        self.last_reminded_at = None
