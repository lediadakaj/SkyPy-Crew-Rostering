"""POST /schedule — run the scheduler on submitted flights + crew."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from skypy.api.errors import bad_request
from skypy.api.state import get_state
from skypy.engine import calculate_layover_costs, generate_schedule
from skypy.io import parse_crew_dict, parse_flight_dict
from skypy.io.exporter import build_output_payload


schedule_bp = Blueprint("schedule", __name__)


@schedule_bp.route("/schedule", methods=["POST"])
def post_schedule():
    if not request.is_json:
        return bad_request("Request body must be JSON with Content-Type: application/json")

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return bad_request("Request body must be a JSON object")

    if "flights" not in data or "crew" not in data:
        return bad_request("Request must include both 'flights' and 'crew' arrays")
    if not isinstance(data["flights"], list) or not isinstance(data["crew"], list):
        return bad_request("'flights' and 'crew' must be arrays")

    try:
        flights = [parse_flight_dict(item) for item in data["flights"]]
        crew_list = [parse_crew_dict(item) for item in data["crew"]]
    except (ValueError, TypeError) as e:
        return bad_request(str(e))

    # Duplicate-ID detection
    seen_flight_ids: set[str] = set()
    for f in flights:
        if f.flight_id in seen_flight_ids:
            return bad_request(f"Duplicate flight_id: {f.flight_id}")
        seen_flight_ids.add(f.flight_id)
    seen_crew_ids: set[str] = set()
    for c in crew_list:
        if c.crew_id in seen_crew_ids:
            return bad_request(f"Duplicate crew_id: {c.crew_id}")
        seen_crew_ids.add(c.crew_id)

    roster, unassigned = generate_schedule(flights, crew_list)
    layover_costs, total_layover_cost = calculate_layover_costs(roster, flights, crew_list)

    # Update shared state so GET /roster and GET /report can read it.
    state = get_state()
    state.roster = roster
    state.flights = flights
    state.crew = crew_list
    state.unassigned = unassigned
    state.layover_costs = layover_costs
    state.total_layover_cost = total_layover_cost
    state.has_run = True

    payload = build_output_payload(
        roster=roster,
        flights=flights,
        crew_list=crew_list,
        unassigned=unassigned,
        layover_costs=layover_costs,
        total_layover_cost=total_layover_cost,
    )
    return jsonify(payload), 200
