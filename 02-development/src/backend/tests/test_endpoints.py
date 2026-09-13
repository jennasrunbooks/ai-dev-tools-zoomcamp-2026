from datetime import datetime, timedelta, timezone

from app import crud


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def add_party(client, **overrides):
    payload = {
        "party_name": "Nguyen",
        "party_size": 4,
        "phone_number": "555-0101",
        "priority": "vip",
        "quoted_wait_minutes": 15,
        "notes": "Corner booth please.",
    }
    payload.update(overrides)
    return client.post("/waitlist", json=payload)


class TestCreateEntry:
    def test_create_entry_returns_201_with_waiting_status(self, client):
        response = add_party(client)
        assert response.status_code == 201
        body = response.json()
        assert body["party_name"] == "Nguyen"
        assert body["status"] == "waiting"
        assert body["sla_breached"] is False
        assert body["notified_at"] is None
        assert body["seated_at"] is None
        assert body["cancelled_at"] is None
        assert "id" in body

    def test_create_entry_defaults_optional_fields_to_null(self, client):
        response = add_party(client, phone_number=None, notes=None)
        body = response.json()
        assert body["phone_number"] is None
        assert body["notes"] is None

    def test_create_entry_missing_required_field_returns_422(self, client):
        response = client.post(
            "/waitlist",
            json={"party_size": 2, "priority": "standard", "quoted_wait_minutes": 10},
        )
        assert response.status_code == 422

    def test_create_entry_invalid_party_size_returns_422(self, client):
        response = add_party(client, party_size=0)
        assert response.status_code == 422

    def test_create_entry_invalid_priority_returns_422(self, client):
        response = add_party(client, priority="platinum")
        assert response.status_code == 422


class TestListEntries:
    def test_list_empty(self, client):
        response = client.get("/waitlist")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_created_entries(self, client):
        add_party(client, party_name="Nguyen")
        add_party(client, party_name="Okafor", priority="standard")
        response = client.get("/waitlist")
        names = [e["party_name"] for e in response.json()]
        assert set(names) == {"Nguyen", "Okafor"}

    def test_list_filters_by_status(self, client):
        created = add_party(client).json()
        client.patch(f"/waitlist/{created['id']}/status", json={"status": "notified"})
        add_party(client, party_name="Untouched")

        response = client.get("/waitlist", params={"status": "notified"})
        body = response.json()
        assert len(body) == 1
        assert body[0]["party_name"] == "Nguyen"

    def test_list_filters_by_priority(self, client):
        add_party(client, party_name="Nguyen", priority="vip")
        add_party(client, party_name="Okafor", priority="standard")

        response = client.get("/waitlist", params={"priority": "standard"})
        body = response.json()
        assert [e["party_name"] for e in body] == ["Okafor"]

    def test_list_filters_by_sla_breached(self, client, db_session):
        add_party(client, party_name="NotBreached", quoted_wait_minutes=1000)
        breached = add_party(client, party_name="Breached", quoted_wait_minutes=1).json()
        entry = crud.get_entry(db_session, breached["id"])
        entry.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db_session.commit()

        response = client.get("/waitlist", params={"sla_breached": "false"})
        assert [e["party_name"] for e in response.json()] == ["NotBreached"]

        response = client.get("/waitlist", params={"sla_breached": "true"})
        assert [e["party_name"] for e in response.json()] == ["Breached"]

    def test_list_orders_by_priority_then_created_at(self, client):
        add_party(client, party_name="Standard1", priority="standard")
        add_party(client, party_name="Overflow1", priority="reservation_overflow")
        add_party(client, party_name="Vip1", priority="vip")

        response = client.get("/waitlist")
        names = [e["party_name"] for e in response.json()]
        assert names == ["Vip1", "Overflow1", "Standard1"]

    def test_closed_entries_sink_below_active_entries(self, client):
        vip = add_party(client, party_name="VipSeated", priority="vip").json()
        add_party(client, party_name="StandardWaiting", priority="standard")
        client.patch(f"/waitlist/{vip['id']}/status", json={"status": "seated"})

        response = client.get("/waitlist")
        names = [e["party_name"] for e in response.json()]
        assert names == ["StandardWaiting", "VipSeated"]


class TestGetEntry:
    def test_get_existing_entry(self, client):
        created = add_party(client).json()
        response = client.get(f"/waitlist/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_missing_entry_returns_404_with_api_error_shape(self, client):
        response = client.get("/waitlist/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "not_found"
        assert "message" in body


class TestUpdateEntry:
    def test_update_editable_fields(self, client):
        created = add_party(client).json()
        response = client.patch(
            f"/waitlist/{created['id']}",
            json={"party_size": 6, "notes": "Updated notes", "quoted_wait_minutes": 30},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["party_size"] == 6
        assert body["notes"] == "Updated notes"
        assert body["quoted_wait_minutes"] == 30

    def test_partial_update_leaves_other_fields_untouched(self, client):
        created = add_party(client).json()
        response = client.patch(f"/waitlist/{created['id']}", json={"party_size": 8})
        body = response.json()
        assert body["party_size"] == 8
        assert body["notes"] == created["notes"]
        assert body["quoted_wait_minutes"] == created["quoted_wait_minutes"]

    def test_update_missing_entry_returns_404(self, client):
        response = client.patch("/waitlist/does-not-exist", json={"party_size": 2})
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"

    def test_update_invalid_party_size_returns_422(self, client):
        created = add_party(client).json()
        response = client.patch(f"/waitlist/{created['id']}", json={"party_size": 0})
        assert response.status_code == 422


class TestDeleteEntry:
    def test_delete_existing_entry(self, client):
        created = add_party(client).json()
        response = client.delete(f"/waitlist/{created['id']}")
        assert response.status_code == 204

        response = client.get(f"/waitlist/{created['id']}")
        assert response.status_code == 404

    def test_delete_missing_entry_returns_404(self, client):
        response = client.delete("/waitlist/does-not-exist")
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"


class TestStatusTransition:
    def test_valid_transition_waiting_to_notified_sets_notified_at(self, client):
        created = add_party(client).json()
        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "notified"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "notified"
        assert body["notified_at"] is not None

    def test_valid_transition_waiting_to_seated_sets_seated_at(self, client):
        created = add_party(client).json()
        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "seated"})
        body = response.json()
        assert body["status"] == "seated"
        assert body["seated_at"] is not None

    def test_valid_transition_to_cancelled_sets_cancelled_at(self, client):
        created = add_party(client).json()
        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "cancelled"})
        body = response.json()
        assert body["status"] == "cancelled"
        assert body["cancelled_at"] is not None

    def test_requeue_notified_to_waiting_clears_notified_at(self, client):
        created = add_party(client).json()
        client.patch(f"/waitlist/{created['id']}/status", json={"status": "notified"})
        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "waiting"})
        body = response.json()
        assert body["status"] == "waiting"
        assert body["notified_at"] is None

    def test_invalid_transition_returns_409_with_api_error_shape(self, client):
        created = add_party(client).json()
        client.patch(f"/waitlist/{created['id']}/status", json={"status": "seated"})

        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "waiting"})
        assert response.status_code == 409
        body = response.json()
        assert body["code"] == "invalid_transition"
        assert "message" in body

    def test_transition_out_of_terminal_state_rejected(self, client):
        created = add_party(client).json()
        client.patch(f"/waitlist/{created['id']}/status", json={"status": "cancelled"})

        response = client.patch(f"/waitlist/{created['id']}/status", json={"status": "notified"})
        assert response.status_code == 409

    def test_transition_missing_entry_returns_404(self, client):
        response = client.patch("/waitlist/does-not-exist/status", json={"status": "notified"})
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"


class TestStats:
    def test_stats_on_empty_waitlist(self, client):
        response = client.get("/waitlist/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["queue_length"] == 0
        assert body["queue_length_by_priority"] == {
            "vip": 0,
            "reservation_overflow": 0,
            "standard": 0,
        }
        assert body["avg_wait_minutes"] == 0
        assert body["sla_breach_count"] == 0

    def test_stats_only_counts_active_entries(self, client):
        active = add_party(client, party_name="Active", priority="vip").json()
        closed = add_party(client, party_name="ToSeat", priority="standard").json()
        client.patch(f"/waitlist/{closed['id']}/status", json={"status": "seated"})

        response = client.get("/waitlist/stats")
        body = response.json()
        assert body["queue_length"] == 1
        assert body["queue_length_by_priority"]["vip"] == 1
        assert body["queue_length_by_priority"]["standard"] == 0

    def test_stats_counts_sla_breaches(self, client, db_session):
        breached = add_party(client, party_name="Breached", quoted_wait_minutes=1).json()
        add_party(client, party_name="NotBreached", quoted_wait_minutes=1000)

        entry = crud.get_entry(db_session, breached["id"])
        entry.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db_session.commit()

        response = client.get("/waitlist/stats")
        body = response.json()
        assert body["sla_breach_count"] == 1
