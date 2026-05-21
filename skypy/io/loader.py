from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Mapping

from skypy.models.crew import Crew
from skypy.models.flight import Flight


REQUIRED_FLIGHT_FIELDS = (
    "flight_id", "origin", "destination", "departure", "arrival",
    "distance_miles", "priority",
)
REQUIRED_CREW_FIELDS = (
    "crew_id", "home_base", "max_range_miles", "role", "hourly_cost",
)


def _require_fields(record: Mapping[str, Any], required: tuple, kind: str) -> None:
    missing = [f for f in required if f not in record or record[f] in (None, "")]
    if missing:
        raise ValueError(f"{kind}: missing required field(s): {', '.join(missing)}")


def _parse_iso8601(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field}: expected ISO 8601 string, got {type(value).__name__}")
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as e:
        raise ValueError(f"{field}: invalid ISO 8601 timestamp {value!r}: {e}") from None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field}: expected integer, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            raise ValueError(f"{field}: expected integer, got {value!r}") from None
    raise ValueError(f"{field}: expected integer, got {type(value).__name__}")


def _parse_float(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field}: expected float, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            raise ValueError(f"{field}: expected float, got {value!r}") from None
    raise ValueError(f"{field}: expected float, got {type(value).__name__}")


def parse_flight_dict(record: Mapping[str, Any]) -> Flight:
    _require_fields(record, REQUIRED_FLIGHT_FIELDS, "Flight")
    return Flight(
        flight_id=str(record["flight_id"]).strip(),
        origin=str(record["origin"]).strip(),
        destination=str(record["destination"]).strip(),
        departure=_parse_iso8601(record["departure"], "departure"),
        arrival=_parse_iso8601(record["arrival"], "arrival"),
        distance_miles=_parse_int(record["distance_miles"], "distance_miles"),
        priority=_parse_int(record["priority"], "priority"),
    )


def parse_crew_dict(record: Mapping[str, Any]) -> Crew:
    _require_fields(record, REQUIRED_CREW_FIELDS, "Crew")
    return Crew(
        crew_id=str(record["crew_id"]).strip(),
        home_base=str(record["home_base"]).strip(),
        max_range_miles=_parse_int(record["max_range_miles"], "max_range_miles"),
        role=str(record["role"]).strip(),
        hourly_cost=_parse_float(record["hourly_cost"], "hourly_cost"),
    )

def load_flights_csv(path: str | Path) -> List[Flight]:

    flights: List[Flight] = []
    seen_ids: set[str] = set()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for line_no, row in enumerate(reader, start=2):  # header is line 1
            try:
                flight = parse_flight_dict(row)
            except ValueError as e:
                raise ValueError(f"{path}:{line_no}: {e}") from None
            if flight.flight_id in seen_ids:
                raise ValueError(
                    f"{path}:{line_no}: duplicate flight_id: {flight.flight_id}"
                )
            seen_ids.add(flight.flight_id)
            flights.append(flight)
    return flights


def load_crew_csv(path: str | Path) -> List[Crew]:
    crew: List[Crew] = []
    seen_ids: set[str] = set()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for line_no, row in enumerate(reader, start=2):
            try:
                member = parse_crew_dict(row)
            except ValueError as e:
                raise ValueError(f"{path}:{line_no}: {e}") from None
            if member.crew_id in seen_ids:
                raise ValueError(
                    f"{path}:{line_no}: duplicate crew_id: {member.crew_id}"
                )
            seen_ids.add(member.crew_id)
            crew.append(member)
    return crew
