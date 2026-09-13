"""Mock "database" for the waitlist domain.

An in-memory, process-lifetime store standing in for the real one (SQLite/
SQLAlchemy, per docs/spec.md 5). Kept behind this narrow interface so routers
never touch storage details directly, and so this module is the only thing
that has to change when a real database is wired in later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone

from app.schemas import NewWaitlistEntryInput, Priority, Status, UpdateWaitlistEntryInput, WaitlistEntry

DEFAULT_RESTAURANT_ID = "default"


@dataclass
class StoredEntry:
    id: str
    party_name: str
    party_size: int
    phone_number: str | None
    priority: Priority
    status: Status
    quoted_wait_minutes: int
    created_at: datetime
    notified_at: datetime | None
    seated_at: datetime | None
    cancelled_at: datetime | None
    notes: str | None
    # Paved for future multi-tenancy (docs/spec.md 9, 9.1) — not exposed on
    # the API response schema yet.
    restaurant_id: str = DEFAULT_RESTAURANT_ID

    def to_schema(self) -> WaitlistEntry:
        data = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "restaurant_id"}
        return WaitlistEntry(**data)


@dataclass
class NotificationLogEntry:
    entry_id: str
    channel: str
    sent_at: datetime


class WaitlistStore:
    """In-memory mock database. Not thread-safe; fine for a single-process
    dev server."""

    def __init__(self) -> None:
        self._entries: dict[str, StoredEntry] = {}
        self._notification_log: list[NotificationLogEntry] = []

    def reset(self) -> None:
        self._entries.clear()
        self._notification_log.clear()

    def list_entries(self) -> list[StoredEntry]:
        return list(self._entries.values())

    def get_entry(self, entry_id: str) -> StoredEntry | None:
        return self._entries.get(entry_id)

    def create_entry(self, data: NewWaitlistEntryInput) -> StoredEntry:
        entry = StoredEntry(
            id=str(uuid.uuid4()),
            party_name=data.party_name.strip(),
            party_size=data.party_size,
            phone_number=(data.phone_number or "").strip() or None,
            priority=data.priority,
            status=Status.waiting,
            quoted_wait_minutes=data.quoted_wait_minutes,
            created_at=datetime.now(timezone.utc),
            notified_at=None,
            seated_at=None,
            cancelled_at=None,
            notes=(data.notes or "").strip() or None,
        )
        self._entries[entry.id] = entry
        return entry

    def update_entry(self, entry_id: str, patch: UpdateWaitlistEntryInput) -> StoredEntry | None:
        entry = self._entries.get(entry_id)
        if entry is None:
            return None
        updates = patch.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(entry, key, value)
        return entry

    def set_status(self, entry_id: str, new_status: Status) -> StoredEntry | None:
        entry = self._entries.get(entry_id)
        if entry is None:
            return None
        now = datetime.now(timezone.utc)
        entry.status = new_status
        if new_status == Status.notified:
            entry.notified_at = now
            self._notification_log.append(
                NotificationLogEntry(entry_id=entry.id, channel="sms", sent_at=now)
            )
        if new_status == Status.seated:
            entry.seated_at = now
        if new_status in (Status.cancelled, Status.no_show):
            entry.cancelled_at = now
        if new_status == Status.waiting:
            entry.notified_at = None
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        return self._entries.pop(entry_id, None) is not None

    def seed_demo_data(self) -> None:
        """Populate example rows for local manual testing (uvicorn / Swagger
        UI, and future frontend integration). Never called in tests."""

        def minutes_ago(minutes: int) -> datetime:
            return datetime.now(timezone.utc) - timedelta(minutes=minutes)

        demo = [
            StoredEntry(
                id=str(uuid.uuid4()),
                party_name="Nguyen",
                party_size=4,
                phone_number="555-0101",
                priority=Priority.vip,
                status=Status.waiting,
                quoted_wait_minutes=15,
                created_at=minutes_ago(6),
                notified_at=None,
                seated_at=None,
                cancelled_at=None,
                notes="Anniversary dinner, requested corner booth.",
            ),
            StoredEntry(
                id=str(uuid.uuid4()),
                party_name="Okafor",
                party_size=2,
                phone_number="555-0102",
                priority=Priority.standard,
                status=Status.waiting,
                quoted_wait_minutes=10,
                created_at=minutes_ago(22),
                notified_at=None,
                seated_at=None,
                cancelled_at=None,
                notes=None,
            ),
            StoredEntry(
                id=str(uuid.uuid4()),
                party_name="Alvarez",
                party_size=6,
                phone_number=None,
                priority=Priority.reservation_overflow,
                status=Status.notified,
                quoted_wait_minutes=20,
                created_at=minutes_ago(18),
                notified_at=minutes_ago(2),
                seated_at=None,
                cancelled_at=None,
                notes="Reservation ran long ahead of them.",
            ),
        ]
        for entry in demo:
            self._entries[entry.id] = entry


store = WaitlistStore()
