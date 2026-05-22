from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Mapping

from skypy.models.crew import Crew
from skypy.models.flight import Flight
from skypy.models.roster import Roster


def build_output_payload(
    roster: Roster,
    flights: List[Flight],
    crew_list: List[Crew],
    unassigned: List[Dict[str, str]],
    layover_costs: Mapping[str, float],
    total_layover_cost: float,
) -> Dict:
    flights_by_id = {f.flight_id: f for f in flights}

    payload: Dict = {}
    for crew in crew_list:
        schedule = roster.get_crew_schedule(crew.crew_id, flights_by_id)
        if not schedule:
            continue

        total_minutes = sum(f.duration_minutes for f in schedule)
        payload[crew.crew_id] = {
            "role": crew.role,
            "flights": [f.flight_id for f in schedule],
            "total_hours": round(total_minutes / 60.0, 2),
            "layover_cost": round(float(layover_costs.get(crew.crew_id, 0.0)), 2),
        }

    payload["unassigned"] = list(unassigned)
    payload["total_layover_cost"] = round(float(total_layover_cost), 2)

    return payload


def write_roster_output(payload: Dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
