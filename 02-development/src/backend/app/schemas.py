from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    vip = "vip"
    reservation_overflow = "reservation_overflow"
    standard = "standard"


class Status(str, Enum):
    waiting = "waiting"
    notified = "notified"
    seated = "seated"
    cancelled = "cancelled"
    no_show = "no_show"


class WaitlistEntry(BaseModel):
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


class WaitlistEntryView(WaitlistEntry):
    sla_breached: bool


class NewWaitlistEntryInput(BaseModel):
    party_name: str = Field(min_length=1)
    party_size: int = Field(ge=1)
    phone_number: str | None = None
    priority: Priority
    quoted_wait_minutes: int = Field(ge=1)
    notes: str | None = None


class UpdateWaitlistEntryInput(BaseModel):
    party_size: int | None = Field(default=None, ge=1)
    quoted_wait_minutes: int | None = Field(default=None, ge=1)
    notes: str | None = None


class StatusTransitionInput(BaseModel):
    status: Status


class QueueLengthByPriority(BaseModel):
    vip: int
    reservation_overflow: int
    standard: int


class WaitlistStats(BaseModel):
    queue_length: int
    queue_length_by_priority: QueueLengthByPriority
    avg_wait_minutes: int
    sla_breach_count: int


class ApiError(BaseModel):
    code: str
    message: str
