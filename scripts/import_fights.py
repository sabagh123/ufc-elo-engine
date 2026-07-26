"""Convert a reusable UFC fight CSV into the Elo engine's stable schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ufc_elo.csv_io import write_fights  # noqa: E402
from ufc_elo.data_import import import_tidytuesday_fights  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Downloaded TidyTuesday ufc_fights.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "ufc_fights.csv",
        help="Destination normalized CSV",
    )
    parser.add_argument(
        "--source-order",
        choices=["main-first", "chronological"],
        default="main-first",
        help="Bout order used by the source CSV",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fights = import_tidytuesday_fights(
        args.input,
        source_order=args.source_order,
    )
    write_fights(args.output, fights)
    print(f"Imported {len(fights)} fights.")
    print(f"Wrote normalized data to {args.output}.")


if __name__ == "__main__":
    main()
