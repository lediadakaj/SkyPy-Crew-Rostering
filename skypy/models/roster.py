from typing import Dict, List, Mapping
from skypy.models.flight import Flight


class Roster:
    def __init__(self) -> None:
        self._assignments: Dict[str, List[str]] = {}

    def assign(self, flight_id: str, crew_id: str) -> None:
        crew_on_flight = self._assignments.setdefault(flight_id, [])
        if crew_id in crew_on_flight:
            raise ValueError(
                f"Crew {crew_id} is already assigned to flight {flight_id}"
            )
        crew_on_flight.append(crew_id)


    def get_flight_crew(self, flight_id: str) -> List[str]:
        return list(self._assignments.get(flight_id, []))

    def assigned_flight_ids(self) -> List[str]:
        return [fid for fid, crew in self._assignments.items() if crew]

    def get_crew_schedule(
        self,
        crew_id: str,
        flights_by_id: Mapping[str, Flight],
    ) -> List[Flight]:
        flights = [
            flights_by_id[fid]
            for fid, crew_list in self._assignments.items()
            if crew_id in crew_list and fid in flights_by_id
        ]
        return sorted(flights, key=lambda f: f.departure)

    def all_assigned_crew_ids(self) -> List[str]:
        seen = set()
        for crew_list in self._assignments.values():
            seen.update(crew_list)
        return sorted(seen)

    def as_dict(self) -> Dict[str, List[str]]:
        return {fid: list(crew) for fid, crew in self._assignments.items()}

    def __repr__(self) -> str:
        return f"Roster({self._assignments!r})"

    def __len__(self) -> int:
        """Number of flights with at least one crew member."""
        return sum(1 for crew in self._assignments.values() if crew)
