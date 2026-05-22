from __future__ import annotations

from typing import Optional

from flask import Flask

from skypy.api.routes import all_blueprints
from skypy.api.state import attach_state


def create_app(config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)

    attach_state(app)
   
    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app


__all__ = ["create_app"]
