from datetime import datetime, timezone

from app.schemas import Priority, Status, WaitlistEntry

ACTIVE_STATUSES = (Status.waiting, Status.notified)

# Priority rank per docs/spec.md 3.3: vip > reservation_overflow > standard.
_PRIORITY_RANK = {
    Priority.vip: 0,
    Priority.reservation_overflow: 1,
    Priority.standard: 2,
}


def is_sla_breached(entry: WaitlistEntry, now: datetime | None = None) -> bool:
    """docs/spec.md 3.4: breached when now - created_at > quoted_wait_minutes,
    only meaningful while the entry is still active in the queue."""
    if entry.status not in ACTIVE_STATUSES:
        return False
    now = now or datetime.now(timezone.utc)
    elapsed_minutes = (now - entry.created_at).total_seconds() / 60
    return elapsed_minutes > entry.quoted_wait_minutes


def _closed_at(entry: WaitlistEntry) -> datetime:
    return entry.seated_at or entry.cancelled_at or entry.created_at


def queue_sort_key(entry: WaitlistEntry) -> tuple:
    """Sort key implementing compareByQueueOrder from
    src/frontend/src/utils/sla.ts: active entries first (by priority rank,
    then created_at ascending), closed entries sink below (most-recently-
    closed first)."""
    is_active = entry.status in ACTIVE_STATUSES
    if is_active:
        return (0, _PRIORITY_RANK[entry.priority], entry.created_at)
    # Closed entries: reverse-chronological (most recent first) within the
    # closed group, which sorts after all active entries.
    return (1, -_closed_at(entry).timestamp(), entry.created_at)
