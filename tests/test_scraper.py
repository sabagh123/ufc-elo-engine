from datetime import date

import pytest

from ufc_elo.models import FightResult
from ufc_elo.scraper import (
    EventSummary,
    ScrapeError,
    parse_completed_events,
    parse_event_page,
)


EVENT_INDEX_HTML = """
<table>
  <tr class="b-statistics__table-row">
    <td>
      <a class="b-link b-link_style_black"
         href="http://ufcstats.com/event-details/new-event">
        New Event
      </a>
      <span class="b-statistics__date">January 02, 2026</span>
    </td>
  </tr>
  <tr class="b-statistics__table-row">
    <td>
      <a class="b-link b-link_style_black"
         href="http://ufcstats.com/event-details/old-event">
        Old Event
      </a>
      <span class="b-statistics__date">November 12, 1993</span>
    </td>
  </tr>
</table>
"""

EVENT_PAGE_HTML = """
<table>
  <tr class="b-fight-details__table-row b-fight-details__table-row__hover"
      data-link="http://ufcstats.com/fight-details/fight-123">
    <td><p>W</p><p>L</p></td>
    <td>
      <p><a class="b-link b-link_style_black"
            href="http://ufcstats.com/fighter-details/a">Fighter A</a></p>
      <p><a class="b-link b-link_style_black"
            href="http://ufcstats.com/fighter-details/b">Fighter B</a></p>
    </td>
    <td><p>0</p><p>0</p></td>
    <td><p>1</p><p>0</p></td>
    <td><p>0</p><p>0</p></td>
    <td><p>1</p><p>0</p></td>
    <td><p>Open Weight</p></td>
    <td><p>Submission</p></td>
    <td><p>1</p></td>
    <td><p>2:00</p></td>
  </tr>
</table>
"""


def test_completed_events_are_returned_oldest_first() -> None:
    events = parse_completed_events(EVENT_INDEX_HTML)

    assert [event.name for event in events] == ["Old Event", "New Event"]
    assert events[0].event_date == date(1993, 11, 12)


def test_event_page_is_normalized_to_fight_model() -> None:
    event = EventSummary(
        name="UFC 1: The Beginning",
        event_date=date(1993, 11, 12),
        url="http://ufcstats.com/event-details/old-event",
    )
    fights = parse_event_page(EVENT_PAGE_HTML, event)

    assert len(fights) == 1
    assert fights[0].fight_id == "fight-123"
    assert fights[0].fighter_a == "Fighter A"
    assert fights[0].fighter_b == "Fighter B"
    assert fights[0].result is FightResult.FIGHTER_A_WIN
    assert fights[0].method == "Submission"


def test_event_bouts_are_reversed_into_chronological_order() -> None:
    event = EventSummary(
        name="Test Event",
        event_date=date(2026, 1, 1),
        url="http://ufcstats.com/event-details/test",
    )
    opening_bout = (
        EVENT_PAGE_HTML
        .replace("<table>", "")
        .replace("</table>", "")
        .replace("fight-123", "opening-bout")
        .replace("Fighter A", "Fighter C")
        .replace("Fighter B", "Fighter D")
    )
    page_with_main_event_first = EVENT_PAGE_HTML.replace(
        "</table>",
        opening_bout + "</table>",
    )

    fights = parse_event_page(page_with_main_event_first, event)

    assert [fight.fight_id for fight in fights] == ["opening-bout", "fight-123"]


def test_empty_event_index_fails_loudly() -> None:
    with pytest.raises(ScrapeError):
        parse_completed_events("<html></html>")


def test_unknown_outcome_fails_loudly() -> None:
    event = EventSummary(
        name="Broken Event",
        event_date=date(2026, 1, 1),
        url="http://ufcstats.com/event-details/broken",
    )
    broken_html = EVENT_PAGE_HTML.replace("<p>W</p><p>L</p>", "<p>?</p><p>?</p>")

    with pytest.raises(ScrapeError):
        parse_event_page(broken_html, event)
