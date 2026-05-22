from __future__ import annotations

from typing import Dict, List, Optional

from skypy.engine.rules import required_rest_minutes, rest_gap_minutes
from skypy.models.crew import CAPTAIN, FIRST_OFFICER, Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


def validate_pairing(
    flight_id: str,
    roster: Roster,
    crew_list: List[Crew],
    flights: Optional[List[Flight]] = None,
) -> List[str]:
    crew_by_id: Dict[str, Crew] = {c.crew_id: c for c in crew_list}
    flights_by_id: Dict[str, Flight] = (
        {f.flight_id: f for f in flights} if flights is not None else {}
    )

    if flights is not None and flight_id not in flights_by_id:
        return [f"Unknown flight_id: {flight_id}"]

    assigned_ids = roster.get_flight_crew(flight_id)
    errors: List[str] = []

    # Resolve assigned crew, flagging anyone in the roster but missing from crew_list
    assigned_crew: List[Crew] = []
    for cid in assigned_ids:
        if cid not in crew_by_id:
            errors.append(f"Unknown crew_id assigned: {cid}")
            continue

        assigned_crew.append(crew_by_id[cid])

    captains = [c for c in assigned_crew if c.role == CAPTAIN]
    first_officers = [c for c in assigned_crew if c.role == FIRST_OFFICER]

    if len(captains) != 1:
        errors.append(
            f"Incomplete Pairing: expected exactly 1 Captain, got {len(captains)}"
        )

    if len(first_officers) < 1:
        errors.append(
            f"Incomplete Pairing: expected at least 1 FirstOfficer, got {len(first_officers)}"
        )

    if flights is None:
        return errors

    flight = flights_by_id[flight_id]

    for crew in assigned_crew:
        # Range Certification
        if flight.distance_miles > crew.max_range_miles:
            errors.append(
                f"Crew {crew.crew_id} fails Range Certification: "
                f"{flight.distance_miles}mi > {crew.max_range_miles}mi"
            )

        # Dynamic Rest (only if flight data is available, otherwise skip)
        schedule = roster.get_crew_schedule(crew.crew_id, flights_by_id)
        prev_flight = _previous_flight_in_schedule(schedule, flight)
        if prev_flight is not None:
            required = required_rest_minutes(prev_flight)
            actual = rest_gap_minutes(prev_flight, flight)
            if actual < required:
                errors.append(
                    f"Crew {crew.crew_id} fails Dynamic Rest: "
                    f"{actual:.0f} min after {prev_flight.flight_id}, need {required} min"
                )

    return errors


def _previous_flight_in_schedule(schedule: List[Flight], current: Flight) -> Flight | None:
    for i, f in enumerate(schedule):
        if f.flight_id == current.flight_id:
            return schedule[i - 1] if i > 0 else None

    return None
