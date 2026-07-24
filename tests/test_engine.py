from datetime import date

import pytest

from ufc_elo.engine import EloEngine
from ufc_elo.models import Fight, FightResult


def make_fight(
    fighter_a: str = "Fighter A",
    fighter_b: str = "Fighter B",
    result: FightResult = FightResult.FIGHTER_A_WIN,
) -> Fight:
    return Fight(
        event_date=date(2026, 1, 1),
        event_name="Test Event",
        fighter_a=fighter_a,
        fighter_b=fighter_b,
        result=result,
    )


def test_equal_fighters_have_even_expected_score() -> None:
    engine = EloEngine()
    assert engine.expected_score(1500, 1500) == pytest.approx(0.5)


def test_first_win_moves_equal_ratings_by_sixteen() -> None:
    engine = EloEngine(k_factor=32)
    engine.process_fight(make_fight())

    assert engine.fighters["Fighter A"].rating == pytest.approx(1516)
    assert engine.fighters["Fighter B"].rating == pytest.approx(1484)
    assert engine.fighters["Fighter A"].wins == 1
    assert engine.fighters["Fighter B"].losses == 1


def test_rating_updates_are_zero_sum() -> None:
    engine = EloEngine()
    initial_total = 3000
    engine.process_fight(make_fight())
    new_total = sum(fighter.rating for fighter in engine.fighters.values())
    assert new_total == pytest.approx(initial_total)


def test_draw_updates_records_without_favoring_equal_fighters() -> None:
    engine = EloEngine()
    engine.process_fight(make_fight(result=FightResult.DRAW))

    assert engine.fighters["Fighter A"].rating == pytest.approx(1500)
    assert engine.fighters["Fighter B"].rating == pytest.approx(1500)
    assert engine.fighters["Fighter A"].draws == 1
    assert engine.fighters["Fighter B"].draws == 1


def test_no_contest_does_not_change_ratings() -> None:
    engine = EloEngine()
    engine.process_fight(make_fight(result=FightResult.NO_CONTEST))

    assert engine.fighters["Fighter A"].rating == pytest.approx(1500)
    assert engine.fighters["Fighter B"].rating == pytest.approx(1500)
    assert engine.fighters["Fighter A"].rated_fights == 0
    assert engine.fighters["Fighter A"].no_contests == 1


def test_process_fights_sorts_oldest_first() -> None:
    newer = make_fight("Fighter A", "Fighter C")
    older = Fight(
        event_date=date(2025, 1, 1),
        event_name="Older Event",
        fighter_a="Fighter B",
        fighter_b="Fighter A",
        result=FightResult.FIGHTER_A_WIN,
    )
    engine = EloEngine()
    engine.process_fights([newer, older])

    assert engine.fighters["Fighter B"].rating > engine.fighters["Fighter C"].rating


def test_rankings_are_sorted_highest_first() -> None:
    engine = EloEngine()
    engine.process_fight(make_fight())
    rankings = engine.rankings()

    assert [fighter.name for fighter in rankings] == ["Fighter A", "Fighter B"]
