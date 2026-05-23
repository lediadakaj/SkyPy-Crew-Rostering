from skypy.engine import generate_schedule, validate_roster
from skypy.engine.scheduler import REASON_NO_PAIR
from skypy.models import Roster


def test_scheduler_rejects_flight_exceeding_crew_range(make_flight, make_crew):
    flight = make_flight(flight_id="FL_LONG", distance_miles=3500, origin="JFK", destination="LHR")
    captain = make_crew(crew_id="CAP1", role="Captain", max_range_miles=2000, home_base="JFK")
    first_officer = make_crew(crew_id="FO1", role="FirstOfficer", max_range_miles=2000, home_base="JFK")

    roster, unassigned = generate_schedule([flight], [captain, first_officer])

    assert roster.get_flight_crew("FL_LONG") == []
    assert len(unassigned) == 1
    assert unassigned[0]["flight_id"] == "FL_LONG"
    assert unassigned[0]["reason"].startswith(REASON_NO_PAIR)
    # Range Certification is the blocking rule for both roles
    assert "Range Certification" in unassigned[0]["reason"]


def test_validate_roster_flags_range_violation(make_flight, make_crew):
    flight = make_flight(flight_id="FL_LONG", distance_miles=3500, origin="JFK", destination="LHR")
    crew = make_crew(crew_id="C1", max_range_miles=2000, home_base="JFK")

    roster = Roster()
    roster.assign(flight.flight_id, crew.crew_id)

    violations = validate_roster(roster, [flight], [crew])
    range_violations = [v for v in violations if v["rule"] == "Range Certification"]
    assert len(range_violations) == 1
    assert range_violations[0]["crew_id"] == "C1"
    assert range_violations[0]["flight_id"] == "FL_LONG"
