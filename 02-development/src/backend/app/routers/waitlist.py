from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.errors import InvalidTransitionError, NotFoundError
from app.schemas import (
    NewWaitlistEntryInput,
    Priority,
    QueueLengthByPriority,
    Status,
    StatusTransitionInput,
    UpdateWaitlistEntryInput,
    WaitlistEntryView,
    WaitlistStats,
)
from app.sla import ACTIVE_STATUSES, is_sla_breached, queue_sort_key
from app.state_machine import is_transition_allowed
from app.store import StoredEntry, store

router = APIRouter(tags=["waitlist"])


def _to_view(entry: StoredEntry) -> WaitlistEntryView:
    schema = entry.to_schema()
    return WaitlistEntryView(**schema.model_dump(), sla_breached=is_sla_breached(schema))


@router.get("/waitlist", response_model=list[WaitlistEntryView])
def list_waitlist_entries(
    status: Status | None = None,
    priority: Priority | None = None,
    sla_breached: bool | None = None,
):
    entries = store.list_entries()
    entries.sort(key=queue_sort_key)
    views = [_to_view(e) for e in entries]

    if status is not None:
        views = [v for v in views if v.status == status]
    if priority is not None:
        views = [v for v in views if v.priority == priority]
    if sla_breached is not None:
        views = [v for v in views if v.sla_breached == sla_breached]

    return views


@router.post("/waitlist", response_model=WaitlistEntryView, status_code=201)
def add_waitlist_entry(data: NewWaitlistEntryInput):
    entry = store.create_entry(data)
    return _to_view(entry)


@router.get("/waitlist/stats", response_model=WaitlistStats)
def get_waitlist_stats():
    active = [e for e in store.list_entries() if e.status in ACTIVE_STATUSES]

    by_priority = {Priority.vip: 0, Priority.reservation_overflow: 0, Priority.standard: 0}
    for entry in active:
        by_priority[entry.priority] += 1

    if active:
        now_ts = datetime.now(timezone.utc)
        total_minutes = sum((now_ts - e.created_at).total_seconds() / 60 for e in active)
        avg_wait_minutes = round(total_minutes / len(active))
    else:
        avg_wait_minutes = 0

    breach_count = sum(1 for e in active if is_sla_breached(e.to_schema()))

    return WaitlistStats(
        queue_length=len(active),
        queue_length_by_priority=QueueLengthByPriority(
            vip=by_priority[Priority.vip],
            reservation_overflow=by_priority[Priority.reservation_overflow],
            standard=by_priority[Priority.standard],
        ),
        avg_wait_minutes=avg_wait_minutes,
        sla_breach_count=breach_count,
    )


@router.get("/waitlist/{entry_id}", response_model=WaitlistEntryView)
def get_waitlist_entry(entry_id: str):
    entry = store.get_entry(entry_id)
    if entry is None:
        raise NotFoundError(entry_id)
    return _to_view(entry)


@router.patch("/waitlist/{entry_id}", response_model=WaitlistEntryView)
def update_waitlist_entry(entry_id: str, patch: UpdateWaitlistEntryInput):
    entry = store.update_entry(entry_id, patch)
    if entry is None:
        raise NotFoundError(entry_id)
    return _to_view(entry)


@router.delete("/waitlist/{entry_id}", status_code=204)
def delete_waitlist_entry(entry_id: str):
    deleted = store.delete_entry(entry_id)
    if not deleted:
        raise NotFoundError(entry_id)
    return Response(status_code=204)


@router.patch("/waitlist/{entry_id}/status", response_model=WaitlistEntryView)
def transition_waitlist_entry_status(entry_id: str, transition: StatusTransitionInput):
    entry = store.get_entry(entry_id)
    if entry is None:
        raise NotFoundError(entry_id)

    if not is_transition_allowed(entry.status, transition.status):
        raise InvalidTransitionError(entry.status.value, transition.status.value, entry.party_name)

    updated = store.set_status(entry_id, transition.status)
    return _to_view(updated)
