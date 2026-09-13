from datetime import datetime, timedelta, timezone

from app.schemas import Priority, Status, WaitlistEntry
from app.sla import is_sla_breached


def make_entry(status=Status.waiting, quoted_wait_minutes=10, created_minutes_ago=0, **overrides):
    defaults = dict(
        id="e-1",
        party_name="Test",
        party_size=2,
        phone_number=None,
        priority=Priority.standard,
        status=status,
        quoted_wait_minutes=quoted_wait_minutes,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=created_minutes_ago),
        notified_at=None,
        seated_at=None,
        cancelled_at=None,
        notes=None,
    )
    defaults.update(overrides)
    return WaitlistEntry(**defaults)


def test_not_breached_when_under_quoted_wait():
    entry = make_entry(quoted_wait_minutes=10, created_minutes_ago=5)
    assert is_sla_breached(entry) is False


def test_breached_when_over_quoted_wait():
    entry = make_entry(quoted_wait_minutes=10, created_minutes_ago=15)
    assert is_sla_breached(entry) is True


def test_boundary_exact_quoted_wait_is_not_breached():
    now = datetime.now(timezone.utc)
    entry = make_entry(quoted_wait_minutes=10, created_minutes_ago=0)
    entry.created_at = now - timedelta(minutes=10)
    assert is_sla_breached(entry, now=now) is False


def test_boundary_just_over_quoted_wait_is_breached():
    now = datetime.now(timezone.utc)
    entry = make_entry(quoted_wait_minutes=10, created_minutes_ago=0)
    entry.created_at = now - timedelta(minutes=10, seconds=1)
    assert is_sla_breached(entry, now=now) is True


def test_seated_entries_never_breached_even_if_over_quoted_wait():
    entry = make_entry(status=Status.seated, quoted_wait_minutes=10, created_minutes_ago=60)
    assert is_sla_breached(entry) is False


def test_notified_entries_can_still_breach():
    entry = make_entry(status=Status.notified, quoted_wait_minutes=5, created_minutes_ago=30)
    assert is_sla_breached(entry) is True


def test_cancelled_and_no_show_never_breached():
    entry = make_entry(status=Status.cancelled, quoted_wait_minutes=5, created_minutes_ago=30)
    assert is_sla_breached(entry) is False
    entry = make_entry(status=Status.no_show, quoted_wait_minutes=5, created_minutes_ago=30)
    assert is_sla_breached(entry) is False
