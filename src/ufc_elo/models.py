"""Data models shared by dataset importers and the Elo engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class FightResult(str, Enum):
    """The normalized result from fighter A's point of view."""

    FIGHTER_A_WIN = "fighter_a_win"
    FIGHTER_B_WIN = "fighter_b_win"
    DRAW = "draw"
    NO_CONTEST = "no_contest"


@dataclass(frozen=True, slots=True)
class Fight:
    """One UFC fight in the chronological input dataset."""

    event_date: date
    event_name: str
    fighter_a: str
    fighter_b: str
    result: FightResult
    event_id: str = ""
    bout_order: int = 0
    fight_id: str = ""
    fighter_a_id: str = ""
    fighter_b_id: str = ""
    weight_class: str = ""
    method: str = ""
    round: str = ""
    time: str = ""
    source_url: str = ""

    def __post_init__(self) -> None:
        if not self.fighter_a.strip() or not self.fighter_b.strip():
            raise ValueError("Both fighter names are required")
        if self.bout_order < 0:
            raise ValueError("bout_order cannot be negative")

        same_source_id = (
            self.fighter_a_id.strip()
            and self.fighter_a_id.strip() == self.fighter_b_id.strip()
        )
        same_name_without_ids = (
            not self.fighter_a_id.strip()
            and not self.fighter_b_id.strip()
            and self.fighter_a.strip().casefold()
            == self.fighter_b.strip().casefold()
        )
        if same_source_id or same_name_without_ids:
            raise ValueError("A fighter cannot fight themself")
