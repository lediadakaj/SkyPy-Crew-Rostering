from skypy.api.routes.health import health_bp
from skypy.api.routes.report import report_bp
from skypy.api.routes.roster import roster_bp
from skypy.api.routes.schedule import schedule_bp

all_blueprints = (schedule_bp, roster_bp, report_bp, health_bp)

__all__ = ["all_blueprints", "schedule_bp", "roster_bp", "report_bp", "health_bp"]
