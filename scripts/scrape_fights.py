"""Scrape completed UFCStats events into the normalized fight CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ufc_elo.scraper import scrape_to_csv  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "ufc_fights.csv",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Limit the run while testing; omit to request every event",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between event requests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fights = scrape_to_csv(
        output_path=args.output,
        maximum_events=args.max_events,
        delay_seconds=args.delay,
    )
    print(f"Wrote {len(fights)} fights to {args.output}.")


if __name__ == "__main__":
    main()
