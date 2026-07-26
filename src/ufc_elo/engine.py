"""A small, explainable Elo implementation for UFC fights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Fight, FightResult


@dataclass(slots=True)
class FighterRating:
    """A fighter's current rating and UFC record seen by the engine."""

    name: str
    rating: float
    fighter_id: str = ""
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0
    rated_fights: int = 0

    @property
    def record(self) -> str:
        return (
            f"{self.wins}-{self.losses}-{self.draws}"
            f" ({self.no_contests} NC)"
        )


class EloEngine:
    """Update UFC fighter ratings one fight at a time.

    Version 1 deliberately uses ordinary Elo:

    * every fighter starts at the same rating;
    * wins, losses, and draws update ratings;
    * no contests do not update ratings;
    * the same K-factor is used for every rated fight.
    """

    def __init__(
        self,
        initial_rating: float = 1500.0,
        k_factor: float = 32.0,
        rating_scale: float = 400.0,
    ) -> None:
        if k_factor <= 0:
            raise ValueError("k_factor must be greater than zero")
        if rating_scale <= 0:
            raise ValueError("rating_scale must be greater than zero")

        self.initial_rating = float(initial_rating)
        self.k_factor = float(k_factor)
        self.rating_scale = float(rating_scale)
        self.fighters: dict[str, FighterRating] = {}

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Return fighter A's expected score against fighter B."""

        exponent = (rating_b - rating_a) / self.rating_scale
        return 1.0 / (1.0 + 10.0**exponent)

    @staticmethod
    def _fighter_key(name: str, fighter_id: str = "") -> str:
        clean_id = fighter_id.strip()
        if clean_id:
            return f"id:{clean_id}"
        return name.strip()

    def get_fighter(
        self,
        name: str,
        fighter_id: str = "",
    ) -> FighterRating:
        """Return an existing fighter or create one at the starting rating."""

        clean_name = name.strip()
        clean_id = fighter_id.strip()
        if not clean_name:
            raise ValueError("Fighter name cannot be empty")

        key = self._fighter_key(clean_name, clean_id)
        if key not in self.fighters:
            self.fighters[key] = FighterRating(
                name=clean_name,
                rating=self.initial_rating,
                fighter_id=clean_id,
            )
        elif clean_id and self.fighters[key].name != clean_name:
            # A stable source ID lets one fighter keep a single rating even if
            # the displayed spelling changes later in the dataset.
            self.fighters[key].name = clean_name
        return self.fighters[key]

    def process_fight(self, fight: Fight) -> None:
        """Apply one fight result to both fighters."""

        key_a = self._fighter_key(fight.fighter_a, fight.fighter_a_id)
        key_b = self._fighter_key(fight.fighter_b, fight.fighter_b_id)
        if key_a == key_b:
            raise ValueError("A fighter cannot fight themself")

        fighter_a = self.get_fighter(fight.fighter_a, fight.fighter_a_id)
        fighter_b = self.get_fighter(fight.fighter_b, fight.fighter_b_id)

        if fight.result is FightResult.NO_CONTEST:
            fighter_a.no_contests += 1
            fighter_b.no_contests += 1
            return

        score_a = {
            FightResult.FIGHTER_A_WIN: 1.0,
            FightResult.FIGHTER_B_WIN: 0.0,
            FightResult.DRAW: 0.5,
        }[fight.result]

        expected_a = self.expected_score(fighter_a.rating, fighter_b.rating)
        rating_change = self.k_factor * (score_a - expected_a)

        # Elo is zero-sum here: one fighter gains exactly what the other loses.
        fighter_a.rating += rating_change
        fighter_b.rating -= rating_change
        fighter_a.rated_fights += 1
        fighter_b.rated_fights += 1

        if fight.result is FightResult.FIGHTER_A_WIN:
            fighter_a.wins += 1
            fighter_b.losses += 1
        elif fight.result is FightResult.FIGHTER_B_WIN:
            fighter_b.wins += 1
            fighter_a.losses += 1
        else:
            fighter_a.draws += 1
            fighter_b.draws += 1

    def process_fights(self, fights: Iterable[Fight]) -> None:
        """Process fights from oldest to newest.

        The input is sorted here so callers cannot accidentally calculate Elo
        backwards from the newest event to the oldest.
        """

        def chronological_key(fight: Fight) -> tuple[object, ...]:
            event_key = fight.event_id or fight.event_name.casefold()
            return (fight.event_date, event_key, fight.bout_order)

        for fight in sorted(fights, key=chronological_key):
            self.process_fight(fight)

    def rankings(self, minimum_fights: int = 0) -> list[FighterRating]:
        """Return fighters ordered by rating, then name."""

        if minimum_fights < 0:
            raise ValueError("minimum_fights cannot be negative")

        eligible = [
            fighter
            for fighter in self.fighters.values()
            if fighter.rated_fights >= minimum_fights
        ]
        return sorted(
            eligible,
            key=lambda fighter: (-fighter.rating, fighter.name.casefold()),
        )
