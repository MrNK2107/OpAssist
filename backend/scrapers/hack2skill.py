import logging
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class Hack2SkillScraper(GenericScraper):
    """Hack2Skill scraper — hackathons from hack2skill.com."""

    platform_name = "Hack2Skill"
    API_URL = "https://hack2skill.com/api/v1/innovator/public/event/public-list"
    RECORDS_PER_PAGE = 50
    MAX_PAGES = 10  # Up to 500 events

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"Hack2Skill stage: calling API {self.API_URL}")
        items = self._fetch_paginated(client)
        logger.info(f"Hack2Skill stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_paginated(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            logger.info(f"Hack2Skill: fetching page {page}")
            items, has_more = self._fetch_page(client, page)

            for item in items:
                url = item.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)

            if not has_more:
                break

        return all_items

    def _fetch_page(self, client: httpx.Client, page: int) -> tuple[list[dict], bool]:
        try:
            response = client.get(
                self.API_URL,
                params={"page": page, "records": self.RECORDS_PER_PAGE},
            )
            if not response.is_success:
                logger.warning(f"Hack2Skill API request failed with status {response.status_code}")
                return [], False
            payload = response.json()
            if not payload.get("success"):
                logger.warning(f"Hack2Skill API returned error: {payload.get('message')}")
                return [], False
            data = payload.get("data", [])
            items = self._parse_items(data)
            has_more = len(data) >= self.RECORDS_PER_PAGE
            return items, has_more
        except Exception as exc:
            logger.warning(f"Hack2Skill API fetch failed: {exc}")
            return [], False

    def _parse_items(self, data: list[dict]) -> list[dict]:
        items = []
        now = datetime.now(timezone.utc)

        for event in data:
            reg_end = event.get("registrationEnd")
            deadline = self._parse_iso_date(reg_end)

            # Skip events with past deadlines
            if deadline:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if deadline_dt < now:
                    continue

            event_url = event.get("eventUrl", "")
            link = f"https://hack2skill.com/event/{event_url}" if event_url else ""

            tags = []
            mode = event.get("mode", "")
            if mode:
                tags.append(mode.lower())
            ticket = event.get("ticket", "")
            if ticket:
                tags.append(ticket.lower())
            participation = event.get("participation", "")
            if participation:
                tags.append(participation.lower())

            items.append({
                "title": event.get("title", "").strip(),
                "organizer": "Hack2Skill",
                "start_date": self._parse_iso_date(event.get("registrationStart")),
                "end_date": self._parse_iso_date(event.get("submissionEnd")) or deadline,
                "date": deadline or "",
                "location": "Online" if mode == "VIRTUAL" else "In-Person" if mode == "IN_PERSON" else mode,
                "link": link,
                "source_platform": "Hack2Skill",
                "description": "",
                "prize": "",
                "tags": tags,
                "difficulty": self._infer_difficulty(tags),
                "type": "hackathon",
                "is_closed": False,
                "image_url": event.get("thumbnail", ""),
            })

        return items

    @staticmethod
    def _parse_iso_date(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None
