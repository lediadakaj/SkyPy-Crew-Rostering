from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


_ALLOWED_PRIORITIES = (1, 2, 3)


@dataclass
class Flight:
    flight_id: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    distance_miles: int
    priority: int

    def __post_init__(self) -> None:
        if self.arrival <= self.departure:
            raise ValueError(
                f"Flight {self.flight_id}: arrival ({self.arrival.isoformat()}) "
                f"must be after departure ({self.departure.isoformat()})"
            )

        if isinstance(self.distance_miles, bool) or not isinstance(self.distance_miles, int):
            raise ValueError(
                f"Flight {self.flight_id}: distance_miles must be an integer, got {type(self.distance_miles).__name__}"
            )
        if self.distance_miles <= 0:
            raise ValueError(
                f"Flight {self.flight_id}: distance_miles must be positive, got {self.distance_miles}"
            )

        if self.priority not in _ALLOWED_PRIORITIES:
            raise ValueError(
                f"Flight {self.flight_id}: priority must be one of {_ALLOWED_PRIORITIES}, got {self.priority}"
            )

    @property
    def duration_minutes(self) -> int:
        return int((self.arrival - self.departure).total_seconds() // 60)
