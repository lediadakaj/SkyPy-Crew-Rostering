from __future__ import annotations

from datetime import timedelta

from skypy.engine import validate_roster
from skypy.models import Roster
from tests.conftest import utc


def test_first_flight_not_from_home_base_is_violation(make_flight, make_crew):
    """Crew home base = JFK but their first flight starts from BOS -> violation."""
    flight = make_flight(
        flight_id="F1", origin="BOS", destination="JFK",
        departure=utc(2024, 2, 1, 8, 0), duration_minutes=90, distance_miles=200,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, crew.crew_id)

    violations = validate_roster(roster, [flight], [crew])
    home_base_violations = [v for v in violations if v["rule"] == "Home Base Start"]
    assert len(home_base_violations) == 1
    assert home_base_violations[0]["crew_id"] == "C1"
    assert home_base_violations[0]["flight_id"] == "F1"


def test_first_flight_from_home_base_passes(make_flight, make_crew):
    flight = make_flight(
        flight_id="F1", origin="JFK", destination="BOS",
        departure=utc(2024, 2, 1, 8, 0), duration_minutes=90, distance_miles=200,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, crew.crew_id)

    violations = validate_roster(roster, [flight], [crew])
    assert [v for v in violations if v["rule"] == "Home Base Start"] == []


def test_destination_must_match_next_origin(make_flight, make_crew):
    """flight[0] lands in BOS but flight[1] departs from MIA -> teleport -> violation."""
    f1 = make_flight(
        flight_id="F1", origin="JFK", destination="BOS",
        departure=utc(2024, 2, 1, 8, 0), duration_minutes=90, distance_miles=200,
    )
    f2 = make_flight(
        flight_id="F2", origin="MIA", destination="JFK",
        departure=f1.arrival + timedelta(hours=3),
        duration_minutes=180, distance_miles=1000,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(f1.flight_id, crew.crew_id)
    roster.assign(f2.flight_id, crew.crew_id)

    violations = validate_roster(roster, [f1, f2], [crew])
    continuity = [v for v in violations if v["rule"] == "Route Continuity"]
    assert len(continuity) == 1
    assert continuity[0]["flight_id"] == "F2"


def test_continuity_satisfied_when_destinations_chain(make_flight, make_crew):
    f1 = make_flight(
        flight_id="F1", origin="JFK", destination="BOS",
        departure=utc(2024, 2, 1, 8, 0), duration_minutes=90, distance_miles=200,
    )
    f2 = make_flight(
        flight_id="F2", origin="BOS", destination="JFK",
        departure=f1.arrival + timedelta(hours=3),
        duration_minutes=90, distance_miles=200,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(f1.flight_id, crew.crew_id)
    roster.assign(f2.flight_id, crew.crew_id)

    violations = validate_roster(roster, [f1, f2], [crew])
    assert [v for v in violations if v["rule"] == "Route Continuity"] == []
