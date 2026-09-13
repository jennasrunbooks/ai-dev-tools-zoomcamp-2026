from datetime import datetime, timedelta, timezone

from app.schemas import Priority, Status, WaitlistEntry
from app.sla import queue_sort_key


def make_entry(entry_id, priority, status=Status.waiting, created_minutes_ago=0, closed_minutes_ago=None, **overrides):
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=entry_id,
        party_name=entry_id,
        party_size=2,
        phone_number=None,
        priority=priority,
        status=status,
        quoted_wait_minutes=15,
        created_at=now - timedelta(minutes=created_minutes_ago),
        notified_at=None,
        seated_at=None,
        cancelled_at=None,
        notes=None,
    )
    if status == Status.seated and closed_minutes_ago is not None:
        defaults["seated_at"] = now - timedelta(minutes=closed_minutes_ago)
    if status in (Status.cancelled, Status.no_show) and closed_minutes_ago is not None:
        defaults["cancelled_at"] = now - timedelta(minutes=closed_minutes_ago)
    defaults.update(overrides)
    return WaitlistEntry(**defaults)


def sorted_ids(entries):
    return [e.id for e in sorted(entries, key=queue_sort_key)]


def test_vip_ranks_above_reservation_overflow_and_standard():
    entries = [
        make_entry("standard-1", Priority.standard, created_minutes_ago=5),
        make_entry("vip-1", Priority.vip, created_minutes_ago=1),
        make_entry("overflow-1", Priority.reservation_overflow, created_minutes_ago=3),
    ]
    assert sorted_ids(entries) == ["vip-1", "overflow-1", "standard-1"]


def test_same_priority_sorted_by_created_at_ascending():
    entries = [
        make_entry("later", Priority.standard, created_minutes_ago=2),
        make_entry("earlier", Priority.standard, created_minutes_ago=20),
        make_entry("middle", Priority.standard, created_minutes_ago=10),
    ]
    assert sorted_ids(entries) == ["earlier", "middle", "later"]


def test_earlier_lower_priority_does_not_jump_ahead_of_later_higher_priority():
    # An old standard party still sorts behind a freshly-checked-in VIP party.
    entries = [
        make_entry("old-standard", Priority.standard, created_minutes_ago=100),
        make_entry("new-vip", Priority.vip, created_minutes_ago=1),
    ]
    assert sorted_ids(entries) == ["new-vip", "old-standard"]


def test_closed_entries_sink_below_all_active_entries_regardless_of_priority():
    entries = [
        make_entry("closed-vip", Priority.vip, status=Status.seated, created_minutes_ago=50, closed_minutes_ago=1),
        make_entry("active-standard", Priority.standard, created_minutes_ago=5),
    ]
    assert sorted_ids(entries) == ["active-standard", "closed-vip"]


def test_closed_entries_sorted_most_recently_closed_first():
    entries = [
        make_entry("closed-old", Priority.standard, status=Status.cancelled, created_minutes_ago=60, closed_minutes_ago=50),
        make_entry("closed-recent", Priority.standard, status=Status.seated, created_minutes_ago=30, closed_minutes_ago=2),
    ]
    assert sorted_ids(entries) == ["closed-recent", "closed-old"]


def test_sla_breach_does_not_reorder_queue():
    # Breach is informational only — it must not jump the queue (docs/spec.md 3.3).
    entries = [
        make_entry("breached-standard", Priority.standard, quoted_wait_minutes=1, created_minutes_ago=30),
        make_entry("fresh-vip", Priority.vip, created_minutes_ago=1),
    ]
    assert sorted_ids(entries) == ["fresh-vip", "breached-standard"]
