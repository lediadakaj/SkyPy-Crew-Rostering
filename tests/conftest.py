"""Shared pytest fixtures and helpers."""

from datetime import datetime, timedelta, timezone

import pytest

from skypy.models import Crew, Flight


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


@pytest.fixture
def make_flight():
    def _make(
        flight_id: str = "FL000",
        origin: str = "JFK",
        destination: str = "BOS",
        departure: datetime | None = None,
        duration_minutes: int = 90,
        distance_miles: int = 200,
        priority: int = 2,
    ) -> Flight:
        dep = departure or utc(2024, 2, 1, 8, 0)
        return Flight(
            flight_id=flight_id,
            origin=origin,
            destination=destination,
            departure=dep,
            arrival=dep + timedelta(minutes=duration_minutes),
            distance_miles=distance_miles,
            priority=priority,
        )
    return _make


@pytest.fixture
def make_crew():
    def _make(
        crew_id: str = "C000",
        home_base: str = "JFK",
        max_range_miles: int = 5000,
        role: str = "Captain",
        hourly_cost: float = 100.0,
    ) -> Crew:
        return Crew(
            crew_id=crew_id,
            home_base=home_base,
            max_range_miles=max_range_miles,
            role=role,
            hourly_cost=hourly_cost,
        )
    return _make
