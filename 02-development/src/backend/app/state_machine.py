from app.schemas import Status

# Mirrors src/frontend/src/utils/statusMachine.ts so the frontend and backend
# can't drift on what counts as a valid transition (docs/spec.md 3.2).
# `waiting -> seated` covers walking a party straight to a table without a
# separate notify step.
ALLOWED_TRANSITIONS: dict[Status, list[Status]] = {
    Status.waiting: [Status.notified, Status.seated, Status.cancelled],
    Status.notified: [Status.seated, Status.no_show, Status.waiting],
    Status.seated: [],
    Status.cancelled: [],
    Status.no_show: [],
}


def next_statuses(current: Status) -> list[Status]:
    return ALLOWED_TRANSITIONS[current]


def is_transition_allowed(from_status: Status, to_status: Status) -> bool:
    return to_status in ALLOWED_TRANSITIONS[from_status]


def is_terminal(status: Status) -> bool:
    return len(ALLOWED_TRANSITIONS[status]) == 0
