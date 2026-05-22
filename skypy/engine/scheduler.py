from __future__ import annotations

import heapq
from typing import Dict, List, Mapping, Optional, Set, Tuple

from skypy.engine.rules import required_rest_minutes, rest_gap_minutes

from skypy.models.crew import CAPTAIN, FIRST_OFFICER, Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


REASON_NO_CAPTAIN = "No Captain available"
REASON_NO_FIRST_OFFICER = "No FirstOfficer available"
REASON_NO_PAIR = "No valid pair found"


def generate_schedule(
    flights: List[Flight],
    crew_list: List[Crew],
) -> Tuple[Roster, List[Dict[str, str]]]:
    
    flights_by_id: Dict[str, Flight] = {f.flight_id: f for f in flights}

    roster = Roster()
    unassigned: List[Dict[str, str]] = []

    # Min-heap: (priority, departure, flight_id, flight).
    heap: List[Tuple[int, object, str, Flight]] = []
    for f in flights:
        heapq.heappush(heap, (f.priority, f.departure, f.flight_id, f))

    while heap:
        _, _, _, flight = heapq.heappop(heap)

        captain, cap_reasons = _find_assignable(
            role=CAPTAIN,
            flight=flight,
            crew_list=crew_list,
            roster=roster,
            flights_by_id=flights_by_id,
        )
        first_officer, fo_reasons = _find_assignable(
            role=FIRST_OFFICER,
            flight=flight,
            crew_list=crew_list,
            roster=roster,
            flights_by_id=flights_by_id,
            exclude_crew_id=captain.crew_id if captain else None,
        )

        if captain is None and first_officer is None:
            reason = _build_reason(
                REASON_NO_PAIR,
                {"Captain": cap_reasons, "FirstOfficer": fo_reasons},
            )
        elif captain is None:
            reason = _build_reason(REASON_NO_CAPTAIN, {"Captain": cap_reasons})
        elif first_officer is None:
            reason = _build_reason(REASON_NO_FIRST_OFFICER, {"FirstOfficer": fo_reasons})
        else:
            roster.assign(flight.flight_id, captain.crew_id)
            roster.assign(flight.flight_id, first_officer.crew_id)
            continue

        unassigned.append({"flight_id": flight.flight_id, "reason": reason})

    return roster, unassigned


def _find_assignable(
    *,
    role: str,
    flight: Flight,
    crew_list: List[Crew],
    roster: Roster,
    flights_by_id: Dict[str, Flight],
    exclude_crew_id: Optional[str] = None,
) -> Tuple[Optional[Crew], Set[str]]:

    candidates = [
        c for c in crew_list
        if c.role == role and (exclude_crew_id is None or c.crew_id != exclude_crew_id)
    ]
    failure_reasons: Set[str] = set()
    for crew in candidates:
        why = _why_cant_assign(crew, flight, roster, flights_by_id)
        if why is None:
            return crew, set()
        failure_reasons.add(why)
    return None, failure_reasons


def _why_cant_assign(
    crew: Crew,
    flight: Flight,
    roster: Roster,
    flights_by_id: Dict[str, Flight],
) -> Optional[str]:

    # Range Certification (per flight, no schedule context needed)
    if flight.distance_miles > crew.max_range_miles:
        return "Range Certification"

    current = roster.get_crew_schedule(crew.crew_id, flights_by_id)

    # Build the prospective schedule
    new_schedule = sorted(current + [flight], key=lambda f: f.departure)
    insert_idx = next(i for i, f in enumerate(new_schedule) if f.flight_id == flight.flight_id)

    # Home Base Start: the FIRST flight in the new schedule must depart from home base.
    if new_schedule[0].origin != crew.home_base:
        return "Home Base Start"

    # Neighbour with previous flight (continuity + rest)
    if insert_idx > 0:
        prev = new_schedule[insert_idx - 1]
        if prev.destination != flight.origin:
            return "Route Continuity"
        if rest_gap_minutes(prev, flight) < required_rest_minutes(prev):
            return "Dynamic Rest"

    # Neighbour with next flight (continuity + rest)
    if insert_idx < len(new_schedule) - 1:
        nxt = new_schedule[insert_idx + 1]
        if flight.destination != nxt.origin:
            return "Route Continuity"
        if rest_gap_minutes(flight, nxt) < required_rest_minutes(flight):
            return "Dynamic Rest"

    return None


def _build_reason(prefix: str, role_failures: Mapping[str, Set[str]]) -> str:
    parts: List[str] = []
    for role, rules in role_failures.items():
        if rules:
            parts.append(f"{role}: {', '.join(sorted(rules))}")
    if not parts:
        return prefix
    return f"{prefix} ({'; '.join(parts)})"
