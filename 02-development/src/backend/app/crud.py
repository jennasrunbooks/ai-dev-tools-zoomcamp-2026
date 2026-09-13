"""DB access layer. Routers only ever call functions here — nothing else
touches a Session or the ORM models directly, so this is the one place that
would need to change for a different persistence strategy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NotificationLogModel, WaitlistEntryModel
from app.schemas import NewWaitlistEntryInput, Priority, Status, UpdateWaitlistEntryInput


def list_entries(db: Session) -> list[WaitlistEntryModel]:
    return list(db.scalars(select(WaitlistEntryModel)).all())


def get_entry(db: Session, entry_id: str) -> WaitlistEntryModel | None:
    return db.get(WaitlistEntryModel, entry_id)


def create_entry(db: Session, data: NewWaitlistEntryInput) -> WaitlistEntryModel:
    entry = WaitlistEntryModel(
        party_name=data.party_name.strip(),
        party_size=data.party_size,
        phone_number=(data.phone_number or "").strip() or None,
        priority=data.priority,
        status=Status.waiting,
        quoted_wait_minutes=data.quoted_wait_minutes,
        notes=(data.notes or "").strip() or None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_entry(db: Session, entry_id: str, patch: UpdateWaitlistEntryInput) -> WaitlistEntryModel | None:
    entry = db.get(WaitlistEntryModel, entry_id)
    if entry is None:
        return None
    for key, value in patch.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def set_status(db: Session, entry_id: str, new_status: Status) -> WaitlistEntryModel | None:
    entry = db.get(WaitlistEntryModel, entry_id)
    if entry is None:
        return None

    now = datetime.now(timezone.utc)
    entry.status = new_status
    if new_status == Status.notified:
        entry.notified_at = now
        db.add(NotificationLogModel(entry_id=entry.id, channel="sms", sent_at=now))
    if new_status == Status.seated:
        entry.seated_at = now
    if new_status in (Status.cancelled, Status.no_show):
        entry.cancelled_at = now
    if new_status == Status.waiting:
        entry.notified_at = None

    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: str) -> bool:
    entry = db.get(WaitlistEntryModel, entry_id)
    if entry is None:
        return False
    db.delete(entry)
    db.commit()
    return True


def list_notification_logs(db: Session, entry_id: str) -> list[NotificationLogModel]:
    return list(
        db.scalars(select(NotificationLogModel).where(NotificationLogModel.entry_id == entry_id)).all()
    )


def seed_demo_data(db: Session) -> None:
    """Populate example rows for local manual testing (uvicorn / Swagger UI,
    and the frontend). Never called in tests. Guarded so restarting the dev
    server doesn't re-seed on top of real persisted data."""
    if db.scalar(select(WaitlistEntryModel).limit(1)) is not None:
        return

    def _minutes_ago(minutes: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)

    demo = [
        WaitlistEntryModel(
            party_name="Nguyen",
            party_size=4,
            phone_number="555-0101",
            priority=Priority.vip,
            status=Status.waiting,
            quoted_wait_minutes=15,
            created_at=_minutes_ago(6),
            notes="Anniversary dinner, requested corner booth.",
        ),
        WaitlistEntryModel(
            party_name="Okafor",
            party_size=2,
            phone_number="555-0102",
            priority=Priority.standard,
            status=Status.waiting,
            quoted_wait_minutes=10,
            created_at=_minutes_ago(22),
        ),
        WaitlistEntryModel(
            party_name="Alvarez",
            party_size=6,
            priority=Priority.reservation_overflow,
            status=Status.notified,
            quoted_wait_minutes=20,
            created_at=_minutes_ago(18),
            notified_at=_minutes_ago(2),
            notes="Reservation ran long ahead of them.",
        ),
    ]
    db.add_all(demo)
    db.commit()
