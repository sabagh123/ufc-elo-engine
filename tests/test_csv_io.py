from datetime import date

from ufc_elo.csv_io import read_fights, write_fights
from ufc_elo.models import Fight, FightResult


def test_fight_csv_round_trip(tmp_path) -> None:
    path = tmp_path / "fights.csv"
    original = [
        Fight(
            event_date=date(1993, 11, 12),
            event_name="Test Event",
            event_id="event-1",
            bout_order=1,
            fight_id="abc123",
            fighter_a_id="fighter-a",
            fighter_a="Fighter A",
            fighter_b_id="fighter-b",
            fighter_b="Fighter B",
            result=FightResult.FIGHTER_A_WIN,
            weight_class="Open Weight",
            method="Submission",
            round="1",
            time="2:00",
            source_url="https://example.test/fights/abc123",
        )
    ]

    write_fights(path, original)

    assert read_fights(path) == original
