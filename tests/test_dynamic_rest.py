from __future__ import annotations

from datetime import timedelta

from skypy.engine import validate_roster
from skypy.models import Roster
from tests.conftest import utc


def _build_pair(make_flight, first_duration: int, gap_minutes: int):
    """Build two back-to-back flights (JFK→BOS, BOS→JFK) with the given gap."""
    first_dep = utc(2024, 2, 1, 8, 0)
    first = make_flight(
        flight_id="F1",
        origin="JFK", destination="BOS",
        departure=first_dep,
        duration_minutes=first_duration,
        distance_miles=100,
    )
    second_dep = first.arrival + timedelta(minutes=gap_minutes)
    second = make_flight(
        flight_id="F2",
        origin="BOS", destination="JFK",
        departure=second_dep,
        duration_minutes=60,
        distance_miles=100,
    )
    return first, second


def test_short_flight_60_minute_gap_is_accepted(make_flight, make_crew):
    first, second = _build_pair(make_flight, first_duration=120, gap_minutes=60)
    crew = make_crew(crew_id="C1", home_base="JFK")
    roster = Roster()
    roster.assign(first.flight_id, crew.crew_id)
    roster.assign(second.flight_id, crew.crew_id)

    violations = validate_roster(roster, [first, second], [crew])
    rest_violations = [v for v in violations if v["rule"] == "Dynamic Rest"]
    assert rest_violations == []


def test_short_flight_59_minute_gap_is_rejected(make_flight, make_crew):
    first, second = _build_pair(make_flight, first_duration=120, gap_minutes=59)
    crew = make_crew(crew_id="C1", home_base="JFK")
    roster = Roster()
    roster.assign(first.flight_id, crew.crew_id)
    roster.assign(second.flight_id, crew.crew_id)

    violations = validate_roster(roster, [first, second], [crew])
    rest_violations = [v for v in violations if v["rule"] == "Dynamic Rest"]
    assert len(rest_violations) == 1
    assert rest_violations[0]["flight_id"] == "F2"


def test_long_flight_120_minute_gap_is_accepted(make_flight, make_crew):
    first, second = _build_pair(make_flight, first_duration=180, gap_minutes=120)
    crew = make_crew(crew_id="C1", home_base="JFK")
    roster = Roster()
    roster.assign(first.flight_id, crew.crew_id)
    roster.assign(second.flight_id, crew.crew_id)

    violations = validate_roster(roster, [first, second], [crew])
    rest_violations = [v for v in violations if v["rule"] == "Dynamic Rest"]
    assert rest_violations == []


def test_long_flight_119_minute_gap_is_rejected(make_flight, make_crew):
    first, second = _build_pair(make_flight, first_duration=180, gap_minutes=119)
    crew = make_crew(crew_id="C1", home_base="JFK")
    roster = Roster()
    roster.assign(first.flight_id, crew.crew_id)
    roster.assign(second.flight_id, crew.crew_id)

    violations = validate_roster(roster, [first, second], [crew])
    rest_violations = [v for v in violations if v["rule"] == "Dynamic Rest"]
    assert len(rest_violations) == 1
    assert rest_violations[0]["flight_id"] == "F2"
