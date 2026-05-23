from datetime import timedelta

from skypy.engine import generate_schedule
from skypy.engine.scheduler import (
    REASON_NO_CAPTAIN,
    REASON_NO_FIRST_OFFICER,
    REASON_NO_PAIR,
)
from tests.conftest import utc


class TestPriorityOrdering:
    def test_priority_1_wins_crew_over_priority_3_at_same_time(self, make_flight, make_crew):
        p1_flight = make_flight(
            flight_id="HIGH", priority=1,
            departure=utc(2024, 2, 1, 8, 0), duration_minutes=90,
            origin="JFK", destination="BOS", distance_miles=200,
        )
        p3_flight = make_flight(
            flight_id="LOW", priority=3,
            departure=utc(2024, 2, 1, 8, 0), duration_minutes=90,
            origin="JFK", destination="BOS", distance_miles=200,
        )
        cap = make_crew(crew_id="CAP", role="Captain")
        fo = make_crew(crew_id="FO", role="FirstOfficer")

        roster, unassigned = generate_schedule([p3_flight, p1_flight], [cap, fo])

        assert roster.get_flight_crew("HIGH") == ["CAP", "FO"]
        assert roster.get_flight_crew("LOW") == []
        assert {u["flight_id"] for u in unassigned} == {"LOW"}

    def test_input_order_does_not_affect_priority_outcome(self, make_flight, make_crew):
        p1 = make_flight(
            flight_id="HIGH", priority=1,
            departure=utc(2024, 2, 1, 8, 0), duration_minutes=90,
            origin="JFK", destination="BOS", distance_miles=200,
        )
        p3 = make_flight(
            flight_id="LOW", priority=3,
            departure=utc(2024, 2, 1, 7, 30), duration_minutes=90,  # earlier
            origin="JFK", destination="BOS", distance_miles=200,
        )
        cap = make_crew(crew_id="CAP", role="Captain")
        fo = make_crew(crew_id="FO", role="FirstOfficer")

        roster, _ = generate_schedule([p3, p1], [cap, fo])
        assert roster.get_flight_crew("HIGH") == ["CAP", "FO"]
        assert roster.get_flight_crew("LOW") == []

    def test_earlier_departure_breaks_priority_ties(self, make_flight, make_crew):
        early = make_flight(
            flight_id="EARLY", priority=2,
            departure=utc(2024, 2, 1, 6, 0), duration_minutes=90,
            origin="JFK", destination="BOS", distance_miles=200,
        )
        late = make_flight(
            flight_id="LATE", priority=2,
            departure=utc(2024, 2, 1, 10, 0), duration_minutes=90,
            origin="JFK", destination="BOS", distance_miles=200,
        )
        cap = make_crew(crew_id="CAP", role="Captain")
        fo = make_crew(crew_id="FO", role="FirstOfficer")

        roster, _ = generate_schedule([late, early], [cap, fo])
        assert roster.get_flight_crew("EARLY") == ["CAP", "FO"]
        assert roster.get_flight_crew("LATE") == []



class TestUnassignmentReasons:
    def test_no_captain_available_reason(self, make_flight, make_crew):
        flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                             distance_miles=200, duration_minutes=90)
        fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK")

        roster, unassigned = generate_schedule([flight], [fo])
        assert roster.get_flight_crew("F1") == []
        assert unassigned == [{"flight_id": "F1", "reason": REASON_NO_CAPTAIN}]

    def test_no_first_officer_available_reason(self, make_flight, make_crew):
        """Only a Captain exists — reason: 'No FirstOfficer available'."""
        flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                             distance_miles=200, duration_minutes=90)
        cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK")

        roster, unassigned = generate_schedule([flight], [cap])
        assert roster.get_flight_crew("F1") == []
        assert unassigned == [{"flight_id": "F1", "reason": REASON_NO_FIRST_OFFICER}]

    def test_no_valid_pair_when_neither_role_qualifies(self, make_flight, make_crew):
        long_haul = make_flight(
            flight_id="F1", origin="JFK", destination="LHR",
            distance_miles=3500, duration_minutes=420,
        )
        cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK", max_range_miles=1000)
        fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK", max_range_miles=1000)

        roster, unassigned = generate_schedule([long_haul], [cap, fo])
        assert roster.get_flight_crew("F1") == []
        assert len(unassigned) == 1
        assert unassigned[0]["flight_id"] == "F1"
        assert unassigned[0]["reason"].startswith(REASON_NO_PAIR)
        assert "Captain: Range Certification" in unassigned[0]["reason"]
        assert "FirstOfficer: Range Certification" in unassigned[0]["reason"]

    def test_empty_crew_yields_no_valid_pair(self, make_flight):
        flight = make_flight(flight_id="F1")
        _, unassigned = generate_schedule([flight], [])
        assert unassigned == [{"flight_id": "F1", "reason": REASON_NO_PAIR}]

    def test_detailed_diagnostic_names_specific_blocking_rule(self, make_flight, make_crew):
        from datetime import timedelta
        prev = make_flight(
            flight_id="PREV", origin="JFK", destination="BOS",
            departure=utc(2024, 2, 1, 8, 0),
            duration_minutes=200, distance_miles=200,  
        )
        
        curr = make_flight(
            flight_id="CURR", origin="BOS", destination="JFK",
            departure=prev.arrival + timedelta(minutes=30),
            duration_minutes=60, distance_miles=200,
        )
        cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK")
        fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK")

        roster, unassigned = generate_schedule([prev, curr], [cap, fo])

        assert roster.get_flight_crew("PREV") == ["CAP", "FO"]
        assert roster.get_flight_crew("CURR") == []
        assert len(unassigned) == 1
        assert unassigned[0]["flight_id"] == "CURR"
        assert "Dynamic Rest" in unassigned[0]["reason"]



class TestAtomicAssignment:
    def test_partial_pair_never_written(self, make_flight, make_crew):
        flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                             distance_miles=200, duration_minutes=90)
        cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK")

        roster, unassigned = generate_schedule([flight], [cap])  

        assert roster.get_flight_crew("F1") == []
        assert len(unassigned) == 1

    def test_successful_pair_assigns_both_crew(self, make_flight, make_crew):
        flight = make_flight(flight_id="F1", origin="JFK", destination="BOS",
                             distance_miles=200, duration_minutes=90)
        cap = make_crew(crew_id="CAP", role="Captain", home_base="JFK")
        fo = make_crew(crew_id="FO", role="FirstOfficer", home_base="JFK")

        roster, unassigned = generate_schedule([flight], [cap, fo])
        crew_on_flight = roster.get_flight_crew("F1")
        assert "CAP" in crew_on_flight
        assert "FO" in crew_on_flight
        assert len(crew_on_flight) == 2
        assert unassigned == []


class TestEmptyInputs:
    def test_no_flights_no_crew(self):
        roster, unassigned = generate_schedule([], [])
        assert len(roster) == 0
        assert unassigned == []

    def test_no_flights_with_crew(self, make_crew):
        cap = make_crew(crew_id="CAP", role="Captain")
        roster, unassigned = generate_schedule([], [cap])
        assert len(roster) == 0
        assert unassigned == []
