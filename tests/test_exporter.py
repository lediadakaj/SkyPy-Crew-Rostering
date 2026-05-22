from __future__ import annotations

import json
from pathlib import Path

from skypy.io.exporter import build_output_payload, write_roster_output
from skypy.models import Roster


def test_payload_has_required_top_level_keys(make_flight, make_crew):
    f = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                    distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK")
    fo = make_crew(crew_id="C2", role="FirstOfficer", home_base="JFK")

    roster = Roster()
    roster.assign(f.flight_id, cap.crew_id)
    roster.assign(f.flight_id, fo.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[cap, fo],
        unassigned=[], layover_costs={}, total_layover_cost=0.0,
    )

    assert "unassigned" in payload
    assert "total_layover_cost" in payload
    assert "C1" in payload
    assert "C2" in payload


def test_each_crew_block_has_required_keys(make_flight, make_crew):
    f = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                    distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK")

    roster = Roster()
    roster.assign(f.flight_id, cap.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[cap],
        unassigned=[], layover_costs={}, total_layover_cost=0.0,
    )

    crew_block = payload["C1"]
    assert set(crew_block.keys()) == {"role", "flights", "total_hours", "layover_cost"}
    assert crew_block["role"] == "Captain"
    assert crew_block["flights"] == ["F1"]
    assert crew_block["total_hours"] == 1.5
    assert crew_block["layover_cost"] == 0.0


def test_total_hours_sums_across_assigned_flights(make_flight, make_crew):
    from datetime import timedelta
    f1 = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                     distance_miles=200, duration_minutes=90)
    f2 = make_flight(
        flight_id="F2", origin="BOS", destination="JFK",
        distance_miles=200, duration_minutes=90,
        departure=f1.arrival + timedelta(hours=3),
    )
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK")

    roster = Roster()
    roster.assign(f1.flight_id, cap.crew_id)
    roster.assign(f2.flight_id, cap.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f1, f2], crew_list=[cap],
        unassigned=[], layover_costs={}, total_layover_cost=0.0,
    )
    assert payload["C1"]["total_hours"] == 3.0


def test_layover_cost_propagates_into_payload(make_flight, make_crew):
    f = make_flight(flight_id="F1", origin="JFK", destination="LAX",
                    distance_miles=2500, duration_minutes=360)
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK",
                    hourly_cost=100.0, max_range_miles=5000)

    roster = Roster()
    roster.assign(f.flight_id, cap.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[cap],
        unassigned=[], layover_costs={"C1": 800.0}, total_layover_cost=800.0,
    )
    assert payload["C1"]["layover_cost"] == 800.0
    assert payload["total_layover_cost"] == 800.0


def test_unassigned_flights_listed_with_reasons(make_flight, make_crew):
    f = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                    distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK")

    roster = Roster()  
    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[cap],
        unassigned=[{"flight_id": "F1", "reason": "No valid pair found"}],
        layover_costs={}, total_layover_cost=0.0,
    )
    assert payload["unassigned"] == [{"flight_id": "F1", "reason": "No valid pair found"}]


def test_crew_with_no_assignments_omitted(make_flight, make_crew):
    f = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                    distance_miles=200, duration_minutes=90)
    flyer = make_crew(crew_id="C1", role="Captain", home_base="JFK")
    bench = make_crew(crew_id="C2", role="Captain", home_base="JFK")

    roster = Roster()
    roster.assign(f.flight_id, flyer.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[flyer, bench],
        unassigned=[], layover_costs={}, total_layover_cost=0.0,
    )
    assert "C1" in payload
    assert "C2" not in payload


def test_write_roster_output_writes_valid_json(make_flight, make_crew, tmp_path: Path):
    f = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                    distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK")

    roster = Roster()
    roster.assign(f.flight_id, cap.crew_id)

    payload = build_output_payload(
        roster=roster, flights=[f], crew_list=[cap],
        unassigned=[], layover_costs={}, total_layover_cost=0.0,
    )
    out = tmp_path / "roster_output.json"
    write_roster_output(payload, out)

    # Must be valid JSON and equal what we wrote
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["C1"]["flights"] == ["F1"]
    assert loaded["total_layover_cost"] == 0.0
