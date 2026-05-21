from __future__ import annotations

from dataclasses import dataclass


CAPTAIN = "Captain"
FIRST_OFFICER = "FirstOfficer"
_ALLOWED_ROLES = (CAPTAIN, FIRST_OFFICER)


@dataclass
class Crew:
    crew_id: str
    home_base: str
    max_range_miles: int
    role: str
    hourly_cost: float

    def __post_init__(self) -> None:
        if self.role not in _ALLOWED_ROLES:
            raise ValueError(
                f"Crew {self.crew_id}: role must be one of {_ALLOWED_ROLES}, got {self.role!r}"
            )

        if isinstance(self.max_range_miles, bool) or not isinstance(self.max_range_miles, int):
            raise ValueError(
                f"Crew {self.crew_id}: max_range_miles must be an integer, got {type(self.max_range_miles).__name__}"
            )
        if self.max_range_miles <= 0:
            raise ValueError(
                f"Crew {self.crew_id}: max_range_miles must be positive, got {self.max_range_miles}"
            )

        if isinstance(self.hourly_cost, bool) or not isinstance(self.hourly_cost, (int, float)):
            raise ValueError(
                f"Crew {self.crew_id}: hourly_cost must be a number, got {type(self.hourly_cost).__name__}"
            )
        if self.hourly_cost <= 0:
            raise ValueError(
                f"Crew {self.crew_id}: hourly_cost must be positive, got {self.hourly_cost}"
            )

        self.hourly_cost = float(self.hourly_cost)
