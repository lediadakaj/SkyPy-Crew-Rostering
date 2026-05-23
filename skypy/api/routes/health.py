from flask import jsonify
from flask_smorest import Blueprint

from skypy.api.openapi import load_doc


health_bp = Blueprint(
    "health",
    __name__,
    description="Health check endpoint to verify service is up.",
)


@health_bp.route("/health", methods=["GET"])
@health_bp.doc(**load_doc("health"))
def get_health():
    return jsonify({"status": "ok"}), 200
