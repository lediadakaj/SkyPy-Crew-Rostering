from __future__ import annotations

from datetime import timedelta

from skypy.engine import calculate_layover_costs
from skypy.models import Roster
from tests.conftest import utc


def test_crew_returning_home_has_no_layover_cost(make_flight, make_crew):
    out = make_flight(
        flight_id="F1", origin="JFK", destination="BOS",
        departure=utc(2024, 2, 1, 8, 0), duration_minutes=90, distance_miles=200,
    )
    home = make_flight(
        flight_id="F2", origin="BOS", destination="JFK",
        departure=out.arrival + timedelta(hours=3),
        duration_minutes=90, distance_miles=200,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", hourly_cost=100.0)

    roster = Roster()
    roster.assign(out.flight_id, crew.crew_id)
    roster.assign(home.flight_id, crew.crew_id)

    costs, total = calculate_layover_costs(roster, [out, home], [crew])
    assert costs == {}
    assert total == 0.0


def test_crew_stranded_away_pays_8x_hourly_rate(make_flight, make_crew):
    one_way = make_flight(
        flight_id="F1", origin="JFK", destination="LAX",
        departure=utc(2024, 2, 1, 7, 0), duration_minutes=360, distance_miles=2500,
    )
    crew = make_crew(crew_id="C1", home_base="JFK", hourly_cost=100.0, max_range_miles=5000)

    roster = Roster()
    roster.assign(one_way.flight_id, crew.crew_id)

    costs, total = calculate_layover_costs(roster, [one_way], [crew])
    assert costs == {"C1": 800.0}  # 100 * 8
    assert total == 800.0


def test_unassigned_crew_does_not_appear_in_result(make_flight, make_crew):
    one_way = make_flight(
        flight_id="F1", origin="JFK", destination="LAX",
        departure=utc(2024, 2, 1, 7, 0), duration_minutes=360, distance_miles=2500,
    )
    flyer = make_crew(crew_id="C1", home_base="JFK", hourly_cost=100.0, max_range_miles=5000)
    spare = make_crew(crew_id="C2", home_base="JFK", hourly_cost=200.0, max_range_miles=5000)

    roster = Roster()
    roster.assign(one_way.flight_id, flyer.crew_id)  # C2 is unassigned

    costs, total = calculate_layover_costs(roster, [one_way], [flyer, spare])
    assert "C2" not in costs
    assert costs == {"C1": 800.0}
    assert total == 800.0


def test_total_is_sum_across_crew(make_flight, make_crew):
    one_way = make_flight(
        flight_id="F1", origin="JFK", destination="LAX",
        departure=utc(2024, 2, 1, 7, 0), duration_minutes=360, distance_miles=2500,
    )
    cap = make_crew(crew_id="C1", role="Captain", home_base="JFK",
                    hourly_cost=100.0, max_range_miles=5000)
    fo = make_crew(crew_id="C2", role="FirstOfficer", home_base="JFK",
                   hourly_cost=75.0, max_range_miles=5000)

    roster = Roster()
    roster.assign(one_way.flight_id, cap.crew_id)
    roster.assign(one_way.flight_id, fo.crew_id)

    costs, total = calculate_layover_costs(roster, [one_way], [cap, fo])
    assert costs == {"C1": 800.0, "C2": 600.0}
    assert total == 1400.0
