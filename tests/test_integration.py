from __future__ import annotations

import json
from pathlib import Path

import pytest

from skypy.engine import (
    calculate_layover_costs,
    generate_schedule,
    validate_roster,
)
from skypy.io import load_crew_csv, load_flights_csv
from skypy.io.exporter import build_output_payload, write_roster_output


REPO_ROOT = Path(__file__).resolve().parents[1]
FLIGHTS_CSV = REPO_ROOT / "data" / "flights.csv"
CREW_CSV = REPO_ROOT / "data" / "crew.csv"


@pytest.fixture(scope="module")
def loaded_data():
    flights = load_flights_csv(FLIGHTS_CSV)
    crew = load_crew_csv(CREW_CSV)
    return flights, crew


@pytest.fixture(scope="module")
def scheduled(loaded_data):
    """Run the full pipeline and reuse the result across tests."""
    flights, crew = loaded_data
    roster, unassigned = generate_schedule(flights, crew)
    layover_costs, total_layover = calculate_layover_costs(roster, flights, crew)
    return {
        "flights": flights,
        "crew": crew,
        "roster": roster,
        "unassigned": unassigned,
        "layover_costs": layover_costs,
        "total_layover": total_layover,
    }


def test_sample_csvs_exist_and_load_cleanly(loaded_data):
    flights, crew = loaded_data
    assert len(flights) > 0
    assert len(crew) > 0


def test_loaded_flights_have_expected_ids(loaded_data):
    """Make sure the sample CSV hasn't drifted from what tests expect."""
    flights, _ = loaded_data
    ids = {f.flight_id for f in flights}
    assert {"FL001", "FL002", "FL003", "FL004", "FL005", "FL006"} <= ids


def test_loaded_crew_have_expected_ids(loaded_data):
    _, crew = loaded_data
    ids = {c.crew_id for c in crew}
    assert {"C001", "C002", "C003", "C004", "C005", "C006"} <= ids


def test_scheduled_roster_has_no_rule_violations(scheduled):
    """The scheduler must never produce a roster that breaks the rules."""
    violations = validate_roster(scheduled["roster"], scheduled["flights"], scheduled["crew"])
    assert violations == [], f"Scheduler produced violations: {violations}"


def test_all_flights_either_assigned_or_in_unassigned_list(scheduled):
    """Every input flight is accounted for in exactly one of the two buckets."""
    assigned = set(scheduled["roster"].assigned_flight_ids())
    unassigned = {u["flight_id"] for u in scheduled["unassigned"]}
    all_input = {f.flight_id for f in scheduled["flights"]}

    assert assigned.isdisjoint(unassigned), "A flight appears in both buckets"
    assert assigned | unassigned == all_input, "Some flight is in neither bucket"


def test_every_assigned_flight_has_exactly_one_captain_and_at_least_one_fo(scheduled):
    from skypy.models.crew import CAPTAIN, FIRST_OFFICER

    crew_by_id = {c.crew_id: c for c in scheduled["crew"]}
    for fid in scheduled["roster"].assigned_flight_ids():
        assigned_ids = scheduled["roster"].get_flight_crew(fid)
        captains = [cid for cid in assigned_ids if crew_by_id[cid].role == CAPTAIN]
        fos = [cid for cid in assigned_ids if crew_by_id[cid].role == FIRST_OFFICER]
        assert len(captains) == 1, f"{fid} has {len(captains)} Captains"
        assert len(fos) >= 1, f"{fid} has no FirstOfficer"


def test_unassigned_reasons_are_from_allowed_set(scheduled):
    from skypy.engine.scheduler import (
        REASON_NO_CAPTAIN, REASON_NO_FIRST_OFFICER, REASON_NO_PAIR,
    )
    allowed_prefixes = (REASON_NO_CAPTAIN, REASON_NO_FIRST_OFFICER, REASON_NO_PAIR)
    for u in scheduled["unassigned"]:
        assert any(u["reason"].startswith(p) for p in allowed_prefixes), \
            f"Unknown reason: {u['reason']}"


def test_sample_data_produces_layover_and_unassigned(scheduled):
    assert scheduled["total_layover"] > 0
    assert len(scheduled["unassigned"]) >= 1


def test_full_export_round_trip(scheduled, tmp_path: Path):
    payload = build_output_payload(
        roster=scheduled["roster"],
        flights=scheduled["flights"],
        crew_list=scheduled["crew"],
        unassigned=scheduled["unassigned"],
        layover_costs=scheduled["layover_costs"],
        total_layover_cost=scheduled["total_layover"],
    )

    out = tmp_path / "roster_output.json"
    write_roster_output(payload, out)
    parsed = json.loads(out.read_text(encoding="utf-8"))

    assert "unassigned" in parsed
    assert "total_layover_cost" in parsed

    crew_blocks = {k: v for k, v in parsed.items()
                   if k not in ("unassigned", "total_layover_cost")}
    assert crew_blocks, "Expected at least one assigned crew block"
    for cid, block in crew_blocks.items():
        assert set(block.keys()) == {"role", "flights", "total_hours", "layover_cost"}
        assert block["role"] in ("Captain", "FirstOfficer")
        assert isinstance(block["flights"], list)
        assert isinstance(block["total_hours"], (int, float))
        assert isinstance(block["layover_cost"], (int, float))

    for u in parsed["unassigned"]:
        assert set(u.keys()) == {"flight_id", "reason"}
