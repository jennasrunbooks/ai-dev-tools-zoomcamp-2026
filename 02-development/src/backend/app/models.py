"""SQLAlchemy ORM models. Column types (String-backed enums, DateTime with
timezone) are chosen to work identically across SQLite and Postgres."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.db import Base
from app.schemas import Priority, Status

DEFAULT_RESTAURANT_ID = "default"


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """DateTime(timezone=True) round-trips as offset-naive on SQLite (unlike
    Postgres), which would silently drop tzinfo. Reattach UTC on the way
    back out so callers always get a tz-aware datetime regardless of
    dialect."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class WaitlistEntryModel(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_new_id)
    party_name: Mapped[str] = mapped_column(String, nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), nullable=False)
    status: Mapped[Status] = mapped_column(SAEnum(Status), nullable=False, default=Status.waiting)
    quoted_wait_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    seated_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    # Paved for future multi-tenancy (docs/spec.md 9, 9.1) — not exposed on
    # the API response schema yet.
    restaurant_id: Mapped[str] = mapped_column(String, nullable=False, default=DEFAULT_RESTAURANT_ID, index=True)

    notification_logs: Mapped[list["NotificationLogModel"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


class NotificationLogModel(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_id: Mapped[str] = mapped_column(ForeignKey("waitlist_entries.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now, nullable=False)

    entry: Mapped[WaitlistEntryModel] = relationship(back_populates="notification_logs")
