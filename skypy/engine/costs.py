from typing import Dict, List, Tuple

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


LAYOVER_HOURS = 8


def calculate_layover_costs(
    roster: Roster,
    flights: List[Flight],
    crew_list: List[Crew],
) -> Tuple[Dict[str, float], float]:
    flights_by_id = {f.flight_id: f for f in flights}

    per_crew: Dict[str, float] = {}
    total = 0.0

    for crew in crew_list:
        schedule = roster.get_crew_schedule(crew.crew_id, flights_by_id)
        if not schedule:
            continue

        last_flight = schedule[-1]
        if last_flight.destination == crew.home_base:
            continue

        cost = crew.hourly_cost * LAYOVER_HOURS
        per_crew[crew.crew_id] = cost
        total += cost

    return per_crew, total
