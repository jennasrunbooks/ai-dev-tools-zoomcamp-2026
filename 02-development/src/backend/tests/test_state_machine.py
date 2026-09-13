import pytest

from app.schemas import Status
from app.state_machine import is_terminal, is_transition_allowed, next_statuses

ALLOWED = [
    (Status.waiting, Status.notified),
    (Status.waiting, Status.seated),
    (Status.waiting, Status.cancelled),
    (Status.notified, Status.seated),
    (Status.notified, Status.no_show),
    (Status.notified, Status.waiting),
]

DISALLOWED = [
    (Status.seated, Status.waiting),
    (Status.seated, Status.notified),
    (Status.seated, Status.cancelled),
    (Status.cancelled, Status.waiting),
    (Status.cancelled, Status.notified),
    (Status.cancelled, Status.seated),
    (Status.no_show, Status.waiting),
    (Status.no_show, Status.notified),
    (Status.no_show, Status.seated),
    (Status.waiting, Status.no_show),
    (Status.notified, Status.cancelled),
]


@pytest.mark.parametrize("from_status,to_status", ALLOWED)
def test_allowed_transitions(from_status, to_status):
    assert is_transition_allowed(from_status, to_status) is True


@pytest.mark.parametrize("from_status,to_status", DISALLOWED)
def test_disallowed_transitions(from_status, to_status):
    assert is_transition_allowed(from_status, to_status) is False


@pytest.mark.parametrize("status", [Status.seated, Status.cancelled, Status.no_show])
def test_terminal_states_have_no_next_statuses(status):
    assert next_statuses(status) == []
    assert is_terminal(status) is True


@pytest.mark.parametrize("status", [Status.waiting, Status.notified])
def test_non_terminal_states(status):
    assert is_terminal(status) is False
    assert len(next_statuses(status)) > 0
