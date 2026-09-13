"""Tests specific to swapping the mock store for a real SQLAlchemy-backed
database: persistence guarantees the in-memory mock could never provide.
Uses its own file-backed engines/sessions (not the shared test_engine in
conftest.py) so it can prove data survives disposing the connection
entirely — i.e. an app restart, not just a fresh request."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.db import Base
from app.schemas import NewWaitlistEntryInput, Priority, Status


def _file_engine(path):
    return create_engine(f"sqlite:///{path}")


def test_data_persists_across_independent_sessions(tmp_path):
    engine = _file_engine(tmp_path / "waitflow_sessions.db")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        entry = crud.create_entry(
            session,
            NewWaitlistEntryInput(
                party_name="Persisted", party_size=2, priority=Priority.standard, quoted_wait_minutes=10
            ),
        )
        entry_id = entry.id

    with Session() as session:
        fetched = crud.get_entry(session, entry_id)
        assert fetched is not None
        assert fetched.party_name == "Persisted"


def test_data_survives_engine_disposal_and_reconnect(tmp_path):
    """Simulates an app restart: dispose the engine entirely, reconnect to
    the same file, and confirm the row is still there."""
    db_path = tmp_path / "waitflow_restart.db"

    engine_a = _file_engine(db_path)
    Base.metadata.create_all(bind=engine_a)
    with sessionmaker(bind=engine_a)() as session:
        crud.create_entry(
            session,
            NewWaitlistEntryInput(
                party_name="SurvivesRestart", party_size=4, priority=Priority.vip, quoted_wait_minutes=5
            ),
        )
    engine_a.dispose()

    engine_b = _file_engine(db_path)
    with sessionmaker(bind=engine_b)() as session:
        entries = crud.list_entries(session)
        assert any(e.party_name == "SurvivesRestart" for e in entries)
    engine_b.dispose()


def test_deleted_entry_does_not_survive_reconnect(tmp_path):
    db_path = tmp_path / "waitflow_delete.db"

    engine_a = _file_engine(db_path)
    Base.metadata.create_all(bind=engine_a)
    with sessionmaker(bind=engine_a)() as session:
        entry = crud.create_entry(
            session,
            NewWaitlistEntryInput(
                party_name="ToDelete", party_size=2, priority=Priority.standard, quoted_wait_minutes=10
            ),
        )
        crud.delete_entry(session, entry.id)
    engine_a.dispose()

    engine_b = _file_engine(db_path)
    with sessionmaker(bind=engine_b)() as session:
        assert crud.list_entries(session) == []
    engine_b.dispose()


def test_notification_log_row_created_on_transition_to_notified(tmp_path):
    engine = _file_engine(tmp_path / "waitflow_notify.db")
    Base.metadata.create_all(bind=engine)

    with sessionmaker(bind=engine)() as session:
        entry = crud.create_entry(
            session,
            NewWaitlistEntryInput(
                party_name="Notify Me", party_size=2, priority=Priority.standard, quoted_wait_minutes=10
            ),
        )
        crud.set_status(session, entry.id, Status.notified)

        logs = crud.list_notification_logs(session, entry.id)
        assert len(logs) == 1
        assert logs[0].channel == "sms"
        assert logs[0].sent_at is not None


def test_seed_demo_data_is_idempotent(tmp_path):
    """Restarting the dev server must not duplicate seed rows on top of
    whatever's already persisted."""
    engine = _file_engine(tmp_path / "waitflow_seed.db")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        crud.seed_demo_data(session)
        first_count = len(crud.list_entries(session))
        assert first_count > 0

    with Session() as session:
        crud.seed_demo_data(session)
        assert len(crud.list_entries(session)) == first_count
