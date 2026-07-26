"""Import reusable fight datasets into the engine's normalized CSV schema."""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .models import Fight, FightResult


TIDYTUESDAY_FIELDS = {
    "fight_url",
    "event_name",
    "date",
    "f1_name",
    "f1_result",
    "f2_name",
    "f2_result",
    "weight_class",
    "method",
    "round",
    "time",
}


class ImportError(ValueError):
    """Raised when a source dataset cannot be normalized safely."""


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _stable_id(prefix: str, values: Iterable[str]) -> str:
    material = "\x1f".join(values).encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", maxsplit=1)[-1] if path else ""


def _normalize_result(
    fighter_1_result: str,
    fighter_2_result: str,
) -> FightResult:
    outcomes = (
        _clean(fighter_1_result).upper(),
        _clean(fighter_2_result).upper(),
    )
    if outcomes in {("W", "L"), ("WIN", "LOSS")}:
        return FightResult.FIGHTER_A_WIN
    if outcomes in {("L", "W"), ("LOSS", "WIN")}:
        return FightResult.FIGHTER_B_WIN
    if outcomes in {("D", "D"), ("DRAW", "DRAW")}:
        return FightResult.DRAW
    if outcomes in {
        ("NC", "NC"),
        ("N/C", "N/C"),
        ("NO CONTEST", "NO CONTEST"),
    }:
        return FightResult.NO_CONTEST
    raise ImportError(f"Unknown fight outcome pair: {outcomes!r}")


def _source_row_to_fight(
    row: dict[str, str],
    *,
    event_id: str,
    bout_order: int,
    row_number: int,
) -> Fight:
    event_date = date.fromisoformat(_clean(row["date"]))
    event_name = _clean(row["event_name"])
    fighter_a = _clean(row["f1_name"])
    fighter_b = _clean(row["f2_name"])
    source_url = _clean(row["fight_url"])
    fight_id = _id_from_url(source_url) or _stable_id(
        "fight",
        [
            event_date.isoformat(),
            event_name,
            fighter_a,
            fighter_b,
            str(row_number),
        ],
    )

    return Fight(
        event_date=event_date,
        event_name=event_name,
        event_id=event_id,
        bout_order=bout_order,
        fight_id=fight_id,
        fighter_a=fighter_a,
        fighter_b=fighter_b,
        result=_normalize_result(row["f1_result"], row["f2_result"]),
        weight_class=_clean(row["weight_class"]),
        method=_clean(row["method"]),
        round=_clean(row["round"]),
        time=_clean(row["time"]),
        source_url=source_url,
    )


def import_tidytuesday_fights(
    path: str | Path,
    *,
    source_order: str = "main-first",
) -> list[Fight]:
    """Normalize the TidyTuesday 2026-07-07 ``ufc_fights.csv`` file.

    The source lists all bouts from the same event together. ``main-first``
    reverses each event group so early tournament bouts are processed in the
    order they occurred. Use ``chronological`` only if the input file has
    already been reordered from opening bout to main event.
    """

    if source_order not in {"main-first", "chronological"}:
        raise ValueError(
            "source_order must be 'main-first' or 'chronological'"
        )

    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = TIDYTUESDAY_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ImportError(
                "Source CSV is missing columns: "
                + ", ".join(sorted(missing))
            )
        rows = list(reader)

    grouped_rows: dict[tuple[str, str], list[tuple[int, dict[str, str]]]]
    grouped_rows = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        event_key = (_clean(row["date"]), _clean(row["event_name"]))
        grouped_rows[event_key].append((row_number, row))

    fights: list[Fight] = []
    seen_fight_ids: set[str] = set()
    for (date_text, event_name), event_rows in grouped_rows.items():
        ordered_rows = (
            list(reversed(event_rows))
            if source_order == "main-first"
            else event_rows
        )
        event_id = _stable_id("event", [date_text, event_name])

        for bout_order, (row_number, row) in enumerate(
            ordered_rows,
            start=1,
        ):
            try:
                fight = _source_row_to_fight(
                    row,
                    event_id=event_id,
                    bout_order=bout_order,
                    row_number=row_number,
                )
            except (ImportError, ValueError) as error:
                raise ImportError(
                    f"Cannot import source row {row_number}: {error}"
                ) from error

            if fight.fight_id in seen_fight_ids:
                raise ImportError(
                    f"Duplicate fight ID {fight.fight_id!r} "
                    f"at source row {row_number}"
                )
            seen_fight_ids.add(fight.fight_id)
            fights.append(fight)

    return sorted(
        fights,
        key=lambda fight: (
            fight.event_date,
            fight.event_id,
            fight.bout_order,
        ),
    )


def combine_fight_datasets(
    *datasets: Iterable[Fight],
) -> list[Fight]:
    """Combine normalized datasets and reject duplicate stable fight IDs."""

    fights: list[Fight] = []
    seen_fight_ids: set[str] = set()
    for dataset in datasets:
        for fight in dataset:
            if fight.fight_id and fight.fight_id in seen_fight_ids:
                raise ImportError(
                    f"Duplicate fight ID across datasets: {fight.fight_id!r}"
                )
            if fight.fight_id:
                seen_fight_ids.add(fight.fight_id)
            fights.append(fight)

    return sorted(
        fights,
        key=lambda fight: (
            fight.event_date,
            fight.event_id or fight.event_name.casefold(),
            fight.bout_order,
        ),
    )
