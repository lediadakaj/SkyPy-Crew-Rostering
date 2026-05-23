from typing import Dict

from flask import Blueprint, jsonify

from skypy.api.state import get_state


report_bp = Blueprint("report", __name__)


@report_bp.route("/report", methods=["GET"])
def get_report():
    state = get_state()
    if not state.has_run:
        return jsonify({
            "flights_scheduled": 0,
            "flights_unassigned": 0,
            "total_layover_cost": 0.0,
            "per_crew": {},
            "note": "No schedule has been generated yet; POST /schedule first",
        }), 200

    flights_by_id = {f.flight_id: f for f in state.flights}
    per_crew: Dict[str, Dict] = {}
    for crew in state.crew:
        schedule = state.roster.get_crew_schedule(crew.crew_id, flights_by_id)
        if not schedule:
            continue

        total_minutes = sum(f.duration_minutes for f in schedule)
        per_crew[crew.crew_id] = {
            "role": crew.role,
            "flights": [f.flight_id for f in schedule],
            "total_hours": round(total_minutes / 60.0, 2),
            "layover_cost": round(float(state.layover_costs.get(crew.crew_id, 0.0)), 2),
        }

    return jsonify({
        "flights_scheduled": len(state.roster),
        "flights_unassigned": len(state.unassigned),
        "unassigned": list(state.unassigned),
        "total_layover_cost": round(float(state.total_layover_cost), 2),
        "per_crew": per_crew,
    }), 200
