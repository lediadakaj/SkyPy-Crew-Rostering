from __future__ import annotations

from datetime import timezone
from pathlib import Path

import pytest

from skypy.io import load_crew_csv, load_flights_csv, parse_crew_dict, parse_flight_dict


class TestParseFlightDict:
    def _good(self):
        return {
            "flight_id": "FL001",
            "origin": "JFK",
            "destination": "BOS",
            "departure": "2024-02-01T08:00:00Z",
            "arrival": "2024-02-01T09:30:00Z",
            "distance_miles": "200",   # CSV-style string
            "priority": "2",
        }

    def test_happy_path(self):
        f = parse_flight_dict(self._good())
        assert f.flight_id == "FL001"
        assert f.distance_miles == 200
        assert f.priority == 2
        assert f.departure.tzinfo == timezone.utc

    def test_strips_whitespace_in_string_fields(self):
        rec = self._good()
        rec["origin"] = "  JFK  "
        rec["destination"] = " BOS"
        f = parse_flight_dict(rec)
        assert f.origin == "JFK"
        assert f.destination == "BOS"

    def test_accepts_numeric_types_alongside_strings(self):
        """When JSON is the source, numeric fields arrive as int/float."""
        rec = self._good()
        rec["distance_miles"] = 200
        rec["priority"] = 1
        f = parse_flight_dict(rec)
        assert f.distance_miles == 200
        assert f.priority == 1

    @pytest.mark.parametrize("missing", [
        "flight_id", "origin", "destination", "departure", "arrival",
        "distance_miles", "priority",
    ])
    def test_missing_field_raises(self, missing):
        rec = self._good()
        del rec[missing]
        with pytest.raises(ValueError, match=missing):
            parse_flight_dict(rec)

    def test_empty_string_field_treated_as_missing(self):
        rec = self._good()
        rec["origin"] = ""
        with pytest.raises(ValueError, match="origin"):
            parse_flight_dict(rec)

    def test_malformed_timestamp_raises(self):
        rec = self._good()
        rec["departure"] = "not-a-date"
        with pytest.raises(ValueError, match="departure"):
            parse_flight_dict(rec)

    def test_non_numeric_distance_miles_raises(self):
        rec = self._good()
        rec["distance_miles"] = "two hundred"
        with pytest.raises(ValueError, match="distance_miles"):
            parse_flight_dict(rec)

    def test_naive_timestamp_normalized_to_utc(self):
        """A timestamp without timezone info should be treated as UTC."""
        rec = self._good()
        rec["departure"] = "2024-02-01T08:00:00"  # no Z, no offset
        rec["arrival"] = "2024-02-01T09:00:00"
        f = parse_flight_dict(rec)
        assert f.departure.tzinfo == timezone.utc

    def test_z_suffix_and_explicit_offset_both_work(self):
        rec = self._good()
        rec["departure"] = "2024-02-01T08:00:00+00:00"
        f = parse_flight_dict(rec)
        assert f.departure.tzinfo == timezone.utc


class TestParseCrewDict:
    def _good(self):
        return {
            "crew_id": "C001",
            "home_base": "JFK",
            "max_range_miles": "5000",
            "role": "Captain",
            "hourly_cost": "120.0",
        }

    def test_happy_path(self):
        c = parse_crew_dict(self._good())
        assert c.crew_id == "C001"
        assert c.max_range_miles == 5000
        assert c.hourly_cost == 120.0
        assert c.role == "Captain"

    @pytest.mark.parametrize("missing", [
        "crew_id", "home_base", "max_range_miles", "role", "hourly_cost",
    ])
    def test_missing_field_raises(self, missing):
        rec = self._good()
        del rec[missing]
        with pytest.raises(ValueError, match=missing):
            parse_crew_dict(rec)

    def test_invalid_role_surfaces_as_value_error(self):
        rec = self._good()
        rec["role"] = "Pilot"
        with pytest.raises(ValueError, match="role"):
            parse_crew_dict(rec)


class TestCsvFileLoaders:
    def test_load_flights_csv_happy_path(self, tmp_path: Path):
        csv_text = (
            "flight_id,origin,destination,departure,arrival,distance_miles,priority\n"
            "FL001,JFK,BOS,2024-02-01T08:00:00Z,2024-02-01T09:30:00Z,200,1\n"
            "FL002,BOS,JFK,2024-02-01T12:00:00Z,2024-02-01T13:30:00Z,200,2\n"
        )
        path = tmp_path / "flights.csv"
        path.write_text(csv_text)

        flights = load_flights_csv(path)
        assert len(flights) == 2
        assert flights[0].flight_id == "FL001"
        assert flights[1].priority == 2

    def test_load_flights_csv_reports_line_number_on_bad_row(self, tmp_path: Path):
        csv_text = (
            "flight_id,origin,destination,departure,arrival,distance_miles,priority\n"
            "FL001,JFK,BOS,2024-02-01T08:00:00Z,2024-02-01T09:30:00Z,200,1\n"
            "FL002,BOS,JFK,2024-02-01T12:00:00Z,2024-02-01T13:30:00Z,200,99\n"  # bad priority
        )
        path = tmp_path / "flights.csv"
        path.write_text(csv_text)

        with pytest.raises(ValueError, match="3.*priority"):
            load_flights_csv(path)

    def test_load_crew_csv_happy_path(self, tmp_path: Path):
        csv_text = (
            "crew_id,home_base,max_range_miles,role,hourly_cost\n"
            "C001,JFK,5000,Captain,120.0\n"
            "C002,JFK,5000,FirstOfficer,85.0\n"
        )
        path = tmp_path / "crew.csv"
        path.write_text(csv_text)

        crew = load_crew_csv(path)
        assert len(crew) == 2
        assert crew[0].role == "Captain"
        assert crew[1].hourly_cost == 85.0

    def test_load_crew_csv_bad_role_reports_line(self, tmp_path: Path):
        csv_text = (
            "crew_id,home_base,max_range_miles,role,hourly_cost\n"
            "C001,JFK,5000,Pilot,120.0\n"
        )
        path = tmp_path / "crew.csv"
        path.write_text(csv_text)
        with pytest.raises(ValueError, match="2.*role"):
            load_crew_csv(path)

    def test_load_handles_utf8_bom(self, tmp_path: Path):
        csv_text = (
            "flight_id,origin,destination,departure,arrival,distance_miles,priority\n"
            "FL001,JFK,BOS,2024-02-01T08:00:00Z,2024-02-01T09:30:00Z,200,1\n"
        )
        path = tmp_path / "flights.csv"
        path.write_text(csv_text, encoding="utf-8-sig")  # writes BOM + UTF-8
        flights = load_flights_csv(path)
        assert flights[0].flight_id == "FL001"

    def test_missing_file_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_flights_csv("/no/such/path.csv")

    def test_duplicate_flight_id_raises(self, tmp_path: Path):
        """Two rows with the same flight_id must be rejected at load time.

        Roster keys on flight_id internally; a duplicate would silently merge
        two distinct flights into one logical assignment slot.
        """
        csv_text = (
            "flight_id,origin,destination,departure,arrival,distance_miles,priority\n"
            "FL001,JFK,LHR,2024-02-01T08:00:00Z,2024-02-01T15:00:00Z,3500,1\n"
            "FL001,JFK,BOS,2024-02-01T09:00:00Z,2024-02-01T10:30:00Z,200,2\n"
        )
        path = tmp_path / "flights.csv"
        path.write_text(csv_text, encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate flight_id: FL001"):
            load_flights_csv(path)

    def test_duplicate_crew_id_raises(self, tmp_path: Path):
        """Two rows with the same crew_id must be rejected at load time."""
        csv_text = (
            "crew_id,home_base,max_range_miles,role,hourly_cost\n"
            "C001,JFK,5000,Captain,120.0\n"
            "C001,LHR,1000,Captain,80.0\n"
        )
        path = tmp_path / "crew.csv"
        path.write_text(csv_text, encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate crew_id: C001"):
            load_crew_csv(path)
