import argparse
import logging
import sys
from pathlib import Path

from skypy.engine import calculate_layover_costs, generate_schedule, validate_roster
from skypy.io import load_crew_csv, load_flights_csv
from skypy.io.exporter import build_output_payload, write_roster_output


logger = logging.getLogger("skypy.cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the SkyPy crew scheduler.")
    p.add_argument("--flights", default="data/flights.csv", help="path to flights CSV")
    p.add_argument("--crew", default="data/crew.csv", help="path to crew CSV")
    p.add_argument("--out", default="roster_output.json", help="output JSON path")
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="logging verbosity (default: INFO)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="shortcut for --log-level WARNING",
    )
    return p.parse_args(argv)


def _configure_logging(level_name: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level_name),
        format="%(message)s",
        stream=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging("WARNING" if args.quiet else args.log_level)

    try:
        flights = load_flights_csv(args.flights)
        crew = load_crew_csv(args.crew)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to load input: %s", e)
        return 1

    logger.info("Loaded %d flights and %d crew members.", len(flights), len(crew))

    roster, unassigned = generate_schedule(flights, crew)
    logger.info("Scheduled %d flights, %d unassigned.", len(roster), len(unassigned))

    violations = validate_roster(roster, flights, crew)
    if violations:
        logger.warning("Scheduler produced violations (this should not happen):")
        for v in violations:
            logger.warning("  - %s", v)

    layover_costs, total_layover = calculate_layover_costs(roster, flights, crew)
    payload = build_output_payload(
        roster=roster,
        flights=flights,
        crew_list=crew,
        unassigned=unassigned,
        layover_costs=layover_costs,
        total_layover_cost=total_layover,
    )

    out_path = Path(args.out)
    write_roster_output(payload, out_path)
    logger.info("Wrote %s", out_path.resolve())
    logger.info("Total layover cost: $%.2f", total_layover)

    if unassigned:
        logger.info("Unassigned flights:")
        for u in unassigned:
            logger.info("  %s: %s", u["flight_id"], u["reason"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
