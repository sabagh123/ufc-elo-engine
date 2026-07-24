"""Data models shared by the scraper and Elo engine."""

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
    fight_id: str = ""
    weight_class: str = ""
    method: str = ""
    round: str = ""
    time: str = ""

    def __post_init__(self) -> None:
        if not self.fighter_a.strip() or not self.fighter_b.strip():
            raise ValueError("Both fighter names are required")
        if self.fighter_a.strip() == self.fighter_b.strip():
            raise ValueError("A fighter cannot fight themself")
