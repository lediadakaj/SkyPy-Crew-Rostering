from typing import Optional

from flask import jsonify
from flask_smorest import Blueprint

from skypy.api.errors import not_found
from skypy.api.openapi import load_doc
from skypy.api.state import get_state
from skypy.models import Crew


roster_bp = Blueprint(
    "roster",
    __name__,
    description="Look up the assigned flights for a specific crew member.",
)


@roster_bp.route("/roster/<crew_id>", methods=["GET"])
@roster_bp.doc(**load_doc("roster"))
def get_roster(crew_id: str):
    state = get_state()
    if not state.has_run:
        return not_found("No schedule has been generated yet; POST /schedule first")

    flights_by_id = {f.flight_id: f for f in state.flights}
    schedule = state.roster.get_crew_schedule(crew_id, flights_by_id)

    crew_obj: Optional[Crew] = next((c for c in state.crew if c.crew_id == crew_id), None)
    if crew_obj is None or not schedule:
        return not_found(f"Crew {crew_id} not found in current roster")

    total_minutes = sum(f.duration_minutes for f in schedule)
    return jsonify({
        "crew_id": crew_id,
        "role": crew_obj.role,
        "flights": [f.flight_id for f in schedule],
        "total_hours": round(total_minutes / 60.0, 2),
        "layover_cost": round(float(state.layover_costs.get(crew_id, 0.0)), 2),
    }), 200
