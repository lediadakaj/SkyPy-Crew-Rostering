from typing import Optional

from flask import Flask
from flask_smorest import Api

from skypy.api.routes import all_blueprints
from skypy.api.state import attach_state


_OPENAPI_DEFAULTS = {
    "API_TITLE": "SkyPy Crew Rostering API",
    "API_VERSION": "v1",
    "OPENAPI_VERSION": "3.0.3",
    "OPENAPI_URL_PREFIX": "/",
    "OPENAPI_SWAGGER_UI_PATH": "/swagger-ui",
    "OPENAPI_SWAGGER_UI_URL": "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    "OPENAPI_JSON_PATH": "openapi.json",
}


def create_app(config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)

    for key, value in _OPENAPI_DEFAULTS.items():
        app.config.setdefault(key, value)

    if config:
        app.config.update(config)

    attach_state(app)

    api = Api(app)
    for bp in all_blueprints:
        api.register_blueprint(bp)

    return app


__all__ = ["create_app"]
