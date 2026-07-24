"""Build Elo rankings from a normalized fight CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ufc_elo.csv_io import read_fights, write_rankings  # noqa: E402
from ufc_elo.engine import EloEngine  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "sample_fights.csv",
        help="Normalized fight CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "rankings.csv",
        help="Destination rankings CSV",
    )
    parser.add_argument("--k-factor", type=float, default=32.0)
    parser.add_argument("--minimum-fights", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fights = read_fights(args.input)
    engine = EloEngine(k_factor=args.k_factor)
    engine.process_fights(fights)
    rankings = engine.rankings(minimum_fights=args.minimum_fights)
    write_rankings(args.output, rankings)

    print(f"Processed {len(fights)} fights.")
    print(f"Wrote {len(rankings)} ranked fighters to {args.output}.")
    print()
    for rank, fighter in enumerate(rankings[:10], start=1):
        print(
            f"{rank:>2}. {fighter.name:<24} "
            f"{fighter.rating:>7.2f}  {fighter.record}"
        )


if __name__ == "__main__":
    main()
