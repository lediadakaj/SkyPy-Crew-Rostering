from typing import Dict, List

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


REST_THRESHOLD_MINUTES = 180
SHORT_FLIGHT_REST_MINUTES = 60
LONG_FLIGHT_REST_MINUTES = 120


def required_rest_minutes(previous_flight: Flight) -> int:
    if previous_flight.duration_minutes >= REST_THRESHOLD_MINUTES:
        return LONG_FLIGHT_REST_MINUTES
    return SHORT_FLIGHT_REST_MINUTES


def rest_gap_minutes(previous_flight: Flight, next_flight: Flight) -> float:
    return (next_flight.departure - previous_flight.arrival).total_seconds() / 60.0


def _violation(crew_id: str, flight_id: str, rule: str, description: str) -> Dict[str, str]:
    return {
        "crew_id": crew_id,
        "flight_id": flight_id,
        "rule": rule,
        "description": description,
    }


def validate_roster(
    roster: Roster,
    flights: List[Flight],
    crew_list: List[Crew],
) -> List[Dict[str, str]]:
    flights_by_id: Dict[str, Flight] = {f.flight_id: f for f in flights}
    violations: List[Dict[str, str]] = []

    for crew in crew_list:
        schedule = roster.get_crew_schedule(crew.crew_id, flights_by_id)
        if not schedule:
            continue

        first = schedule[0]
        if first.origin != crew.home_base:
            violations.append(_violation(
                crew.crew_id,
                first.flight_id,
                "Home Base Start",
                f"first flight departs from {first.origin}, "
                f"but crew home base is {crew.home_base}",
            ))

        for i, flight in enumerate(schedule):
            # Range Certification (per flight)
            if flight.distance_miles > crew.max_range_miles:
                violations.append(_violation(
                    crew.crew_id,
                    flight.flight_id,
                    "Range Certification",
                    f"flight distance {flight.distance_miles}mi exceeds "
                    f"crew certification {crew.max_range_miles}mi",
                ))

            if i == 0:
                continue

            prev = schedule[i - 1]

            # Route Continuity
            if prev.destination != flight.origin:
                violations.append(_violation(
                    crew.crew_id,
                    flight.flight_id,
                    "Route Continuity",
                    f"previous flight {prev.flight_id} arrived at {prev.destination}, "
                    f"but this flight departs from {flight.origin}",
                ))

            # Dynamic Rest
            required = required_rest_minutes(prev)
            actual = rest_gap_minutes(prev, flight)
            if actual < required:
                violations.append(_violation(
                    crew.crew_id,
                    flight.flight_id,
                    "Dynamic Rest",
                    f"only {actual:.0f} min between {prev.flight_id} arrival and "
                    f"{flight.flight_id} departure; need {required} min after a "
                    f"{prev.duration_minutes}-min flight",
                ))

    return violations
