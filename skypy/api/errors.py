from typing import Tuple

from flask import jsonify


def bad_request(message: str) -> Tuple:
    return jsonify({"error": message}), 400


def not_found(message: str) -> Tuple:
    return jsonify({"error": message}), 404
