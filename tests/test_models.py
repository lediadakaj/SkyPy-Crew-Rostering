from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from skypy.models import Crew, Flight, Roster
from tests.conftest import utc


class TestFlightValidation:
    def test_arrival_before_departure_raises(self):
        with pytest.raises(ValueError, match="arrival"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 10, 0),
                arrival=utc(2024, 2, 1, 9, 0),  # before departure
                distance_miles=200, priority=1,
            )

    def test_arrival_equal_to_departure_raises(self):
        same = utc(2024, 2, 1, 10, 0)
        with pytest.raises(ValueError, match="arrival"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=same, arrival=same,
                distance_miles=200, priority=1,
            )

    def test_zero_distance_miles_raises(self):
        with pytest.raises(ValueError, match="distance_miles"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 8, 0),
                arrival=utc(2024, 2, 1, 9, 0),
                distance_miles=0, priority=1,
            )

    def test_negative_distance_miles_raises(self):
        with pytest.raises(ValueError, match="distance_miles"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 8, 0),
                arrival=utc(2024, 2, 1, 9, 0),
                distance_miles=-100, priority=1,
            )

    def test_non_integer_distance_miles_raises(self):
        with pytest.raises(ValueError, match="distance_miles"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 8, 0),
                arrival=utc(2024, 2, 1, 9, 0),
                distance_miles=200.5,  # float, not int
                priority=1,
            )

    def test_bool_distance_miles_rejected(self):
        """bool is a subclass of int in Python; we explicitly reject it."""
        with pytest.raises(ValueError, match="distance_miles"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 8, 0),
                arrival=utc(2024, 2, 1, 9, 0),
                distance_miles=True,  # bool
                priority=1,
            )

    @pytest.mark.parametrize("bad_priority", [0, 4, -1, 99])
    def test_invalid_priority_raises(self, bad_priority):
        with pytest.raises(ValueError, match="priority"):
            Flight(
                flight_id="F1", origin="JFK", destination="BOS",
                departure=utc(2024, 2, 1, 8, 0),
                arrival=utc(2024, 2, 1, 9, 0),
                distance_miles=200, priority=bad_priority,
            )

    @pytest.mark.parametrize("good_priority", [1, 2, 3])
    def test_valid_priorities_accepted(self, good_priority):
        """All three valid priority values must construct cleanly."""
        Flight(
            flight_id="F1", origin="JFK", destination="BOS",
            departure=utc(2024, 2, 1, 8, 0),
            arrival=utc(2024, 2, 1, 9, 0),
            distance_miles=200, priority=good_priority,
        )


class TestFlightDurationMinutes:
    """Property tests for Flight.duration_minutes."""

    @pytest.mark.parametrize("minutes", [1, 60, 90, 179, 180, 360, 480])
    def test_duration_minutes_matches_arrival_minus_departure(self, minutes):
        dep = utc(2024, 2, 1, 8, 0)
        f = Flight(
            flight_id="F1", origin="JFK", destination="BOS",
            departure=dep, arrival=dep + timedelta(minutes=minutes),
            distance_miles=100, priority=2,
        )
        assert f.duration_minutes == minutes

    def test_duration_minutes_floors_seconds(self):
        """We floor to whole minutes — no off-by-one at rest thresholds."""
        dep = utc(2024, 2, 1, 8, 0)
        f = Flight(
            flight_id="F1", origin="JFK", destination="BOS",
            departure=dep,
            arrival=dep + timedelta(minutes=90, seconds=59),
            distance_miles=100, priority=2,
        )
        assert f.duration_minutes == 90


class TestCrewValidation:
    @pytest.mark.parametrize("bad_role", ["captain", "CAPTAIN", "FO", "Pilot", "", " Captain"])
    def test_invalid_role_raises(self, bad_role):
        with pytest.raises(ValueError, match="role"):
            Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
                 role=bad_role, hourly_cost=100.0)

    @pytest.mark.parametrize("good_role", ["Captain", "FirstOfficer"])
    def test_valid_roles_accepted(self, good_role):
        Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
             role=good_role, hourly_cost=100.0)

    def test_zero_hourly_cost_raises(self):
        with pytest.raises(ValueError, match="hourly_cost"):
            Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
                 role="Captain", hourly_cost=0.0)

    def test_negative_hourly_cost_raises(self):
        with pytest.raises(ValueError, match="hourly_cost"):
            Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
                 role="Captain", hourly_cost=-50.0)

    def test_bool_hourly_cost_rejected(self):
        with pytest.raises(ValueError, match="hourly_cost"):
            Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
                 role="Captain", hourly_cost=True)

    def test_int_hourly_cost_is_normalized_to_float(self):
        """Integers are accepted (JSON often has them) and normalized to float."""
        c = Crew(crew_id="C1", home_base="JFK", max_range_miles=5000,
                 role="Captain", hourly_cost=85)  # int, not float
        assert isinstance(c.hourly_cost, float)
        assert c.hourly_cost == 85.0

    @pytest.mark.parametrize("bad_range", [0, -100, 1.5, True])
    def test_invalid_max_range_miles_raises(self, bad_range):
        with pytest.raises(ValueError, match="max_range_miles"):
            Crew(crew_id="C1", home_base="JFK", max_range_miles=bad_range,
                 role="Captain", hourly_cost=100.0)



class TestRosterPublicAPI:
    def test_empty_roster_has_no_assignments(self):
        r = Roster()
        assert r.get_flight_crew("F1") == []
        assert r.assigned_flight_ids() == []
        assert len(r) == 0

    def test_get_flight_crew_returns_copy_not_internal_list(self):
        """Returned lists must not let callers mutate roster state."""
        r = Roster()
        r.assign("F1", "C1")
        snapshot = r.get_flight_crew("F1")
        snapshot.append("HACKED")
        assert r.get_flight_crew("F1") == ["C1"]

    def test_get_crew_schedule_sorted_by_departure(self, make_flight):
        """Schedule must always come back in chronological order."""
        later = make_flight(flight_id="LATE", departure=utc(2024, 2, 5, 10, 0))
        earlier = make_flight(
            flight_id="EARLY", departure=utc(2024, 2, 1, 8, 0),
            origin="JFK", destination="BOS",
        )

        r = Roster()
        r.assign(later.flight_id, "C1")
        r.assign(earlier.flight_id, "C1")

        flights_by_id = {f.flight_id: f for f in [earlier, later]}
        schedule = r.get_crew_schedule("C1", flights_by_id)
        assert [f.flight_id for f in schedule] == ["EARLY", "LATE"]

    def test_assigned_flight_ids_lists_only_filled_flights(self):
        r = Roster()
        r.assign("F1", "C1")
        r.assign("F2", "C1")
        assert sorted(r.assigned_flight_ids()) == ["F1", "F2"]

    def test_all_assigned_crew_ids_returns_distinct_sorted(self):
        r = Roster()
        r.assign("F1", "C2")
        r.assign("F1", "C1")
        r.assign("F2", "C1") 
        assert r.all_assigned_crew_ids() == ["C1", "C2"]
