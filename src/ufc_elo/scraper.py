"""Polite scraper for completed UFCStats event result pages."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .csv_io import write_fights
from .models import Fight, FightResult


COMPLETED_EVENTS_URL = (
    "http://ufcstats.com/statistics/events/completed?page=all"
)
ALLOWED_HOSTS = {"ufcstats.com", "www.ufcstats.com"}


class ScrapeError(RuntimeError):
    """Raised when UFCStats markup cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class EventSummary:
    name: str
    event_date: date
    url: str


def _clean_text(tag: Tag) -> str:
    return " ".join(tag.stripped_strings)


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%B %d, %Y").date()
    except ValueError as error:
        raise ScrapeError(f"Unexpected UFCStats date: {value!r}") from error


def _id_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", maxsplit=1)[-1]


def parse_completed_events(html: str) -> list[EventSummary]:
    """Parse the UFCStats completed-events index."""

    soup = BeautifulSoup(html, "html.parser")
    events: list[EventSummary] = []

    for row in soup.select("tr.b-statistics__table-row"):
        link = row.select_one(
            "a.b-link.b-link_style_black[href*='/event-details/']"
        )
        date_tag = row.select_one("span.b-statistics__date")
        if link is None or date_tag is None:
            continue

        url = str(link.get("href", "")).strip()
        name = _clean_text(link)
        if not url or not name:
            continue

        events.append(
            EventSummary(
                name=name,
                event_date=_parse_date(_clean_text(date_tag)),
                url=url,
            )
        )

    if not events:
        raise ScrapeError("No completed events found; UFCStats markup may have changed")

    # UFCStats displays newest first, while Elo must be calculated oldest first.
    return sorted(events, key=lambda event: event.event_date)


def _cell_lines(cell: Tag) -> list[str]:
    lines = [_clean_text(item) for item in cell.find_all("p")]
    return [line for line in lines if line]


def _normalize_result(outcomes: list[str]) -> FightResult:
    normalized = [value.strip().upper() for value in outcomes[:2]]
    if normalized in (["W", "L"], ["WIN", "LOSS"]):
        return FightResult.FIGHTER_A_WIN
    if normalized in (["L", "W"], ["LOSS", "WIN"]):
        return FightResult.FIGHTER_B_WIN
    if normalized in (["D", "D"], ["DRAW", "DRAW"]):
        return FightResult.DRAW
    if normalized in (["NC", "NC"], ["N/C", "N/C"]):
        return FightResult.NO_CONTEST
    raise ScrapeError(f"Unknown fight outcome: {outcomes!r}")


def parse_event_page(html: str, event: EventSummary) -> list[Fight]:
    """Parse every fight row from one completed event page."""

    soup = BeautifulSoup(html, "html.parser")
    fights: list[Fight] = []

    rows = soup.select(
        "tr.b-fight-details__table-row"
        "[data-link*='/fight-details/']"
    )
    # UFCStats displays the main event first. Elo needs the actual event
    # sequence, so process the card from its first bout to its main event.
    rows.reverse()
    for row in rows:
        cells = row.find_all("td", recursive=False)
        fighter_links = row.select(
            "a.b-link.b-link_style_black[href*='/fighter-details/']"
        )
        if len(cells) < 10 or len(fighter_links) < 2:
            raise ScrapeError(
                f"Unexpected fight row in {event.name}; UFCStats markup may have changed"
            )

        outcomes = _cell_lines(cells[0])
        fighter_a = _clean_text(fighter_links[0])
        fighter_b = _clean_text(fighter_links[1])
        fight_url = str(row.get("data-link", "")).strip()

        fights.append(
            Fight(
                event_date=event.event_date,
                event_name=event.name,
                fight_id=_id_from_url(fight_url),
                fighter_a=fighter_a,
                fighter_b=fighter_b,
                result=_normalize_result(outcomes),
                weight_class=_clean_text(cells[6]),
                method=_clean_text(cells[7]),
                round=_clean_text(cells[8]),
                time=_clean_text(cells[9]),
            )
        )

    if not fights:
        raise ScrapeError(f"No fights found for completed event {event.name!r}")
    return fights


class UFCStatsClient:
    """Download UFCStats pages with validation and a fixed polite delay."""

    def __init__(
        self,
        delay_seconds: float = 1.0,
        timeout_seconds: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")

        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "ufc-elo-engine/0.1 "
                    "(portfolio research project; "
                    "https://github.com/sabagh123/ufc-elo-engine)"
                )
            }
        )

    def _get(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"Refusing to request unexpected host: {url}")

        response = self.session.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def completed_events(self) -> list[EventSummary]:
        return parse_completed_events(self._get(COMPLETED_EVENTS_URL))

    def fights(
        self,
        events: Iterable[EventSummary],
    ) -> list[Fight]:
        all_fights: list[Fight] = []
        for event in events:
            time.sleep(self.delay_seconds)
            all_fights.extend(parse_event_page(self._get(event.url), event))
        return all_fights

    def scrape(self, maximum_events: int | None = None) -> list[Fight]:
        events = self.completed_events()
        if maximum_events is not None:
            if maximum_events <= 0:
                raise ValueError("maximum_events must be greater than zero")
            events = events[:maximum_events]
        return self.fights(events)


def scrape_to_csv(
    output_path: str | Path,
    maximum_events: int | None = None,
    delay_seconds: float = 1.0,
) -> list[Fight]:
    """Scrape fights and save the normalized CSV."""

    fights = UFCStatsClient(delay_seconds=delay_seconds).scrape(maximum_events)
    write_fights(output_path, fights)
    return fights
