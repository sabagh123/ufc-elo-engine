import csv

import pytest

from ufc_elo.data_import import ImportError, import_tidytuesday_fights
from ufc_elo.models import FightResult


FIELDS = [
    "fight_url",
    "event_name",
    "date",
    "location",
    "f1_name",
    "f1_result",
    "f2_name",
    "f2_result",
    "weight_class",
    "method",
    "round",
    "time",
]


def write_source(path, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def source_row(
    fight_id: str,
    fighter_a: str,
    fighter_b: str,
    result_a: str = "W",
    result_b: str = "L",
) -> dict[str, str]:
    return {
        "fight_url": f"http://example.test/fight-details/{fight_id}",
        "event_name": "Test Event",
        "date": "1993-11-12",
        "location": "Test City",
        "f1_name": fighter_a,
        "f1_result": result_a,
        "f2_name": fighter_b,
        "f2_result": result_b,
        "weight_class": "Open Weight",
        "method": "Decision",
        "round": "1",
        "time": "5:00",
    }


def test_import_normalizes_results_and_ids(tmp_path) -> None:
    path = tmp_path / "source.csv"
    write_source(path, [source_row("fight-1", "A", "B")])

    fights = import_tidytuesday_fights(path)

    assert len(fights) == 1
    assert fights[0].fight_id == "fight-1"
    assert fights[0].event_id.startswith("event-")
    assert fights[0].bout_order == 1
    assert fights[0].result is FightResult.FIGHTER_A_WIN
    assert fights[0].source_url.endswith("/fight-1")


def test_main_first_source_is_reversed_per_event(tmp_path) -> None:
    path = tmp_path / "source.csv"
    write_source(
        path,
        [
            source_row("main-event", "A", "B"),
            source_row("opening-bout", "C", "D"),
        ],
    )

    fights = import_tidytuesday_fights(path, source_order="main-first")

    assert [fight.fight_id for fight in fights] == [
        "opening-bout",
        "main-event",
    ]
    assert [fight.bout_order for fight in fights] == [1, 2]


def test_import_handles_draw_and_no_contest(tmp_path) -> None:
    path = tmp_path / "source.csv"
    write_source(
        path,
        [
            source_row("draw", "A", "B", "D", "D"),
            source_row("nc", "C", "D", "NC", "NC"),
        ],
    )

    fights = import_tidytuesday_fights(path)

    assert {fight.result for fight in fights} == {
        FightResult.DRAW,
        FightResult.NO_CONTEST,
    }


def test_unknown_result_fails_with_source_row(tmp_path) -> None:
    path = tmp_path / "source.csv"
    write_source(path, [source_row("broken", "A", "B", "?", "?")])

    with pytest.raises(ImportError, match="source row 2"):
        import_tidytuesday_fights(path)


def test_missing_columns_fail_loudly(tmp_path) -> None:
    path = tmp_path / "source.csv"
    path.write_text("date,event_name\n1993-11-12,Test\n", encoding="utf-8")

    with pytest.raises(ImportError, match="missing columns"):
        import_tidytuesday_fights(path)
