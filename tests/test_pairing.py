from __future__ import annotations

from datetime import timedelta

from skypy.engine import validate_pairing
from skypy.models import Roster
from tests.conftest import utc


def test_two_captains_no_first_officer_fails_pairing(make_flight, make_crew):
    flight = make_flight(flight_id="FL_PAIR", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    cap_a = make_crew(crew_id="CAP_A", role="Captain", home_base="JFK", max_range_miles=5000)
    cap_b = make_crew(crew_id="CAP_B", role="Captain", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, cap_a.crew_id)
    roster.assign(flight.flight_id, cap_b.crew_id)

    errors = validate_pairing(flight.flight_id, roster, [cap_a, cap_b], [flight])
    assert errors, "Two Captains + no FirstOfficer must produce errors"
    assert any("Captain" in e and "2" in e for e in errors), f"Expected too-many-Captains error in {errors}"
    assert any("FirstOfficer" in e for e in errors), f"Expected missing-FirstOfficer error in {errors}"



def test_valid_pairing_returns_no_errors(make_flight, make_crew):
    flight = make_flight(flight_id="FL_OK", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=5000)
    fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, cap.crew_id)
    roster.assign(flight.flight_id, fo.crew_id)

    errors = validate_pairing(flight.flight_id, roster, [cap, fo], [flight])
    assert errors == []



def test_captain_but_no_first_officer_is_incomplete(make_flight, make_crew):
    """Brief: 'A flight that has a Captain but no FirstOfficer ... must be flagged as Incomplete Pairing'."""
    flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, cap.crew_id)

    errors = validate_pairing(flight.flight_id, roster, [cap], [flight])
    assert errors
    assert any("FirstOfficer" in e for e in errors)


def test_first_officer_but_no_captain_is_incomplete(make_flight, make_crew):
    """Inverse of the above — also Incomplete Pairing."""
    flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, fo.crew_id)

    errors = validate_pairing(flight.flight_id, roster, [fo], [flight])
    assert errors
    assert any("Captain" in e for e in errors)


def test_captain_plus_multiple_first_officers_is_valid(make_flight, make_crew):
    """'At least 1 FirstOfficer' means 2 is also fine."""
    flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=5000)
    fo_a = make_crew(crew_id="FO_A", role="FirstOfficer", home_base="JFK", max_range_miles=5000)
    fo_b = make_crew(crew_id="FO_B", role="FirstOfficer", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, cap.crew_id)
    roster.assign(flight.flight_id, fo_a.crew_id)
    roster.assign(flight.flight_id, fo_b.crew_id)

    errors = validate_pairing(flight.flight_id, roster, [cap, fo_a, fo_b], [flight])
    assert errors == []


def test_range_violation_surfaces_at_pairing_level(make_flight, make_crew):
    """Crew on the flight that fail individual range cert must be flagged."""
    long_haul = make_flight(flight_id="F1", origin="JFK", destination="LHR",
                            distance_miles=3500, duration_minutes=420)
    cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=1000)
    fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK", max_range_miles=1000)

    roster = Roster()
    roster.assign(long_haul.flight_id, cap.crew_id)
    roster.assign(long_haul.flight_id, fo.crew_id)

    errors = validate_pairing(long_haul.flight_id, roster, [cap, fo], [long_haul])
    assert any("Range" in e and "CAP" in e for e in errors)
    assert any("Range" in e and "FO" in e for e in errors)


def test_dynamic_rest_violation_surfaces_at_pairing_level(make_flight, make_crew):
    """Crew with insufficient rest from a previous flight must be flagged on this one."""
    prev = make_flight(
        flight_id="PREV", origin="JFK", destination="BOS",
        departure=utc(2024, 2, 1, 8, 0),
        duration_minutes=200,  # long flight => 120 min rest required
        distance_miles=200,
    )
    curr = make_flight(
        flight_id="CURR", origin="BOS", destination="JFK",
        departure=prev.arrival + timedelta(minutes=30),  # only 30 min rest
        duration_minutes=90, distance_miles=200,
    )
    cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=5000)
    fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(prev.flight_id, cap.crew_id)
    roster.assign(prev.flight_id, fo.crew_id)
    roster.assign(curr.flight_id, cap.crew_id)
    roster.assign(curr.flight_id, fo.crew_id)

    errors = validate_pairing(curr.flight_id, roster, [cap, fo], [prev, curr])
    assert any("Dynamic Rest" in e for e in errors)


def test_unknown_flight_id_returns_error(make_flight, make_crew):
    cap = make_crew(crew_id="CAP", role="Captain")
    fo = make_crew(crew_id="FO", role="FirstOfficer")
    roster = Roster()

    errors = validate_pairing("DOES_NOT_EXIST", roster, [cap, fo], [])
    assert errors
    assert "Unknown flight_id" in errors[0]



def test_brief_three_arg_signature_runs_role_count_checks(make_flight, make_crew):
    flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                         distance_miles=200, duration_minutes=90)
    cap_a = make_crew(crew_id="CAP_A", role="Captain", home_base="JFK", max_range_miles=5000)
    cap_b = make_crew(crew_id="CAP_B", role="Captain", home_base="JFK", max_range_miles=5000)

    roster = Roster()
    roster.assign(flight.flight_id, cap_a.crew_id)
    roster.assign(flight.flight_id, cap_b.crew_id)

    # Brief-matching 3-arg call (no `flights`)
    errors = validate_pairing(flight.flight_id, roster, [cap_a, cap_b])
    assert any("Captain" in e and "2" in e for e in errors)
    assert any("FirstOfficer" in e for e in errors)
