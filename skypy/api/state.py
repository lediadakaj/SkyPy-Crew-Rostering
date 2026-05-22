from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from flask import Flask, current_app

from skypy.models import Crew, Flight, Roster


@dataclass
class LastRun:
    """Holds the most recent scheduling result. Mutated by POST /schedule."""
    roster: Roster = field(default_factory=Roster)
    flights: List[Flight] = field(default_factory=list)
    crew: List[Crew] = field(default_factory=list)
    unassigned: List[Dict[str, str]] = field(default_factory=list)
    layover_costs: Dict[str, float] = field(default_factory=dict)
    total_layover_cost: float = 0.0
    has_run: bool = False


_EXT_KEY = "skypy_state"


def attach_state(app: Flask) -> LastRun:
    state = LastRun()
    app.extensions[_EXT_KEY] = state
    return state


def get_state() -> LastRun:
    return current_app.extensions[_EXT_KEY]
