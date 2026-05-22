from __future__ import annotations

import pytest

from skypy.api import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_payload():
    """A complete request body that produces a successful schedule."""
    return {
        "flights": [
            {
                "flight_id": "F1",
                "origin": "JFK",
                "destination": "BOS",
                "departure": "2024-02-01T08:00:00Z",
                "arrival": "2024-02-01T09:30:00Z",
                "distance_miles": 200,
                "priority": 1,
            }
        ],
        "crew": [
            {"crew_id": "C1", "home_base": "JFK", "max_range_miles": 5000,
             "role": "Captain", "hourly_cost": 100.0},
            {"crew_id": "C2", "home_base": "JFK", "max_range_miles": 5000,
             "role": "FirstOfficer", "hourly_cost": 80.0},
        ],
    }


def test_post_schedule_returns_200_and_full_payload(client, sample_payload):
    resp = client.post("/schedule", json=sample_payload)

    assert resp.status_code == 200
    body = resp.get_json()
    assert "C1" in body and "C2" in body
    assert body["C1"]["flights"] == ["F1"]
    assert body["C1"]["role"] == "Captain"
    assert body["C2"]["role"] == "FirstOfficer"
    assert body["unassigned"] == []
    assert "total_layover_cost" in body


def test_post_schedule_400_when_body_is_not_json(client):
    resp = client.post("/schedule", data="not json", content_type="text/plain")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_post_schedule_400_when_missing_keys(client):
    resp = client.post("/schedule", json={"flights": []})
    assert resp.status_code == 400
    assert "crew" in resp.get_json()["error"]


def test_post_schedule_400_when_field_invalid(client, sample_payload):
    """Field-level validation must surface as 400 with a useful message."""
    sample_payload["crew"][0]["role"] = "Captian"  # typo — invalid role
    resp = client.post("/schedule", json=sample_payload)
    assert resp.status_code == 400
    assert "role" in resp.get_json()["error"]


def test_post_schedule_400_when_arrays_are_wrong_type(client):
    resp = client.post("/schedule", json={"flights": "not a list", "crew": []})
    assert resp.status_code == 400


def test_post_schedule_400_when_duplicate_flight_id(client, sample_payload):
    """API must reject a POST body with two flights sharing flight_id."""
    sample_payload["flights"].append(dict(sample_payload["flights"][0]))
    resp = client.post("/schedule", json=sample_payload)
    assert resp.status_code == 400
    assert "Duplicate flight_id" in resp.get_json()["error"]


def test_post_schedule_400_when_duplicate_crew_id(client, sample_payload):
    """Same rule applies to crew_id."""
    sample_payload["crew"].append(dict(sample_payload["crew"][0]))
    resp = client.post("/schedule", json=sample_payload)
    assert resp.status_code == 400
    assert "Duplicate crew_id" in resp.get_json()["error"]


def test_get_roster_200_for_assigned_crew(client, sample_payload):
    client.post("/schedule", json=sample_payload)
    resp = client.get("/roster/C1")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["crew_id"] == "C1"
    assert body["flights"] == ["F1"]
    assert body["role"] == "Captain"
    assert body["total_hours"] == 1.5


def test_get_roster_404_for_unknown_crew(client, sample_payload):
    client.post("/schedule", json=sample_payload)
    resp = client.get("/roster/DOES_NOT_EXIST")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_get_roster_404_before_any_schedule_run(client):
    resp = client.get("/roster/C1")
    assert resp.status_code == 404


def test_get_report_200_after_schedule(client, sample_payload):
    client.post("/schedule", json=sample_payload)
    resp = client.get("/report")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["flights_scheduled"] == 1
    assert body["flights_unassigned"] == 0
    assert "C1" in body["per_crew"]
    assert "total_layover_cost" in body


def test_get_report_200_with_empty_state_before_schedule(client):
    """Report is callable even before any run — returns zeros, not an error."""
    resp = client.get("/report")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["flights_scheduled"] == 0
    assert body["flights_unassigned"] == 0
    assert body["per_crew"] == {}


def test_get_health_returns_200_without_any_schedule_run(client):
    """Health is a liveness probe, works regardless of scheduler state."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_get_health_returns_200_after_schedule_run(client, sample_payload):
    client.post("/schedule", json=sample_payload)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_apps_are_isolated_from_each_other(sample_payload):
    """Two app instances must not share state — the factory guarantees this."""
    app_a = create_app({"TESTING": True})
    app_b = create_app({"TESTING": True})

    with app_a.test_client() as c_a:
        c_a.post("/schedule", json=sample_payload)

    with app_b.test_client() as c_b:
        resp = c_b.get("/roster/C1")
        assert resp.status_code == 404
