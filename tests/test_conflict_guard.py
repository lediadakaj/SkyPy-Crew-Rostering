from __future__ import annotations

import pytest

from skypy.models import Roster


def test_assigning_same_crew_twice_raises():
    roster = Roster()
    roster.assign("FL001", "C001")
    with pytest.raises(ValueError, match="already assigned"):
        roster.assign("FL001", "C001")


def test_different_crew_on_same_flight_is_fine():
    roster = Roster()
    roster.assign("FL001", "C001")
    roster.assign("FL001", "C002")  # different crew member, must succeed
    assert roster.get_flight_crew("FL001") == ["C001", "C002"]


def test_same_crew_on_different_flights_is_fine():
    roster = Roster()
    roster.assign("FL001", "C001")
    roster.assign("FL002", "C001")  # same crew, different flight fine
    assert roster.get_flight_crew("FL001") == ["C001"]
    assert roster.get_flight_crew("FL002") == ["C001"]
