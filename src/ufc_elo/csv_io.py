"""Read fight data and write ranking output as CSV files."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Iterable

from .engine import FighterRating
from .models import Fight, FightResult


FIGHT_FIELDS = [
    "event_date",
    "event_name",
    "event_id",
    "bout_order",
    "fight_id",
    "fighter_a_id",
    "fighter_a",
    "fighter_b_id",
    "fighter_b",
    "result",
    "weight_class",
    "method",
    "round",
    "time",
    "source_url",
]


def write_fights(path: str | Path, fights: Iterable[Fight]) -> None:
    """Write fights using the project's stable CSV schema."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIGHT_FIELDS)
        writer.writeheader()
        for fight in fights:
            writer.writerow(
                {
                    "event_date": fight.event_date.isoformat(),
                    "event_name": fight.event_name,
                    "event_id": fight.event_id,
                    "bout_order": fight.bout_order,
                    "fight_id": fight.fight_id,
                    "fighter_a_id": fight.fighter_a_id,
                    "fighter_a": fight.fighter_a,
                    "fighter_b_id": fight.fighter_b_id,
                    "fighter_b": fight.fighter_b,
                    "result": fight.result.value,
                    "weight_class": fight.weight_class,
                    "method": fight.method,
                    "round": fight.round,
                    "time": fight.time,
                    "source_url": fight.source_url,
                }
            )


def read_fights(path: str | Path) -> list[Fight]:
    """Read fights from a project CSV file."""

    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = set(FIGHT_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Fight CSV is missing columns: " + ", ".join(sorted(missing))
            )

        return [
            Fight(
                event_date=date.fromisoformat(row["event_date"]),
                event_name=row["event_name"],
                event_id=row["event_id"],
                bout_order=int(row["bout_order"] or 0),
                fight_id=row["fight_id"],
                fighter_a_id=row["fighter_a_id"],
                fighter_a=row["fighter_a"],
                fighter_b_id=row["fighter_b_id"],
                fighter_b=row["fighter_b"],
                result=FightResult(row["result"]),
                weight_class=row["weight_class"],
                method=row["method"],
                round=row["round"],
                time=row["time"],
                source_url=row["source_url"],
            )
            for row in reader
        ]


def write_rankings(
    path: str | Path,
    rankings: Iterable[FighterRating],
) -> None:
    """Write a human-readable rankings table."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "fighter_id",
        "fighter",
        "rating",
        "record",
        "rated_fights",
        "no_contests",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for rank, fighter in enumerate(rankings, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "fighter_id": fighter.fighter_id,
                    "fighter": fighter.name,
                    "rating": f"{fighter.rating:.2f}",
                    "record": fighter.record,
                    "rated_fights": fighter.rated_fights,
                    "no_contests": fighter.no_contests,
                }
            )
