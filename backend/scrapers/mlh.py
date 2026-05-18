import logging
import json
import html
import re
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class MLHScraper(GenericScraper):
    """MLH scraper — hackathons from the MLH season events page."""

    platform_name = "MLH"
    URL = "https://www.mlh.com/seasons/2026/events"

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"MLH stage: fetching {self.URL}")
        response = client.get(self.URL)
        if not response.is_success:
            logger.warning(f"MLH request failed with status {response.status_code}")
            return []

        data = self._extract_data_page(response.text)
        if not data:
            return []

        items = self._parse_events(data)
        logger.info(f"MLH stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _extract_data_page(self, html_text: str) -> dict | None:
        """Extract and parse the data-page JSON attribute."""
        match = re.search(r'data-page="({.*?})"\s*>', html_text, re.DOTALL)
        if not match:
            logger.warning("MLH: data-page attribute not found")
            return None

        raw = html.unescape(match.group(1))
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"MLH: failed to parse data-page JSON: {e}")
            return None

    def _parse_events(self, data: dict) -> list[dict]:
        items: list[dict] = []
        props = data.get("props", {})
        now = datetime.now(timezone.utc)

        upcoming = props.get("upcomingEvents") or []
        if not upcoming:
            logger.info("MLH: no upcoming events found")
            return []

        for event in upcoming:
            if not isinstance(event, dict):
                continue

            title = (event.get("name") or "").strip()
            if not title:
                continue

            starts_at = event.get("startsAt")
            ends_at = event.get("endsAt")

            deadline = self._parse_iso_date(starts_at) if starts_at else None

            # Skip if already started
            if deadline:
                try:
                    dt = datetime.fromisoformat(deadline).replace(tzinfo=timezone.utc)
                    if dt < now:
                        continue
                except ValueError:
                    pass

            slug = event.get("slug", "")
            link = event.get("websiteUrl") or f"https://mlh.io/events/{slug}"

            location = event.get("location") or "Online"
            format_type = event.get("formatType", "")

            tags = []
            if format_type:
                tags.append(format_type)
            region = event.get("region", "")
            if region:
                tags.append(region)

            items.append({
                "title": title,
                "organizer": "Major League Hacking",
                "start_date": self._parse_iso_date(starts_at) if starts_at else None,
                "end_date": self._parse_iso_date(ends_at) if ends_at else None,
                "date": deadline,
                "location": location,
                "link": link,
                "source_platform": "MLH",
                "description": "",
                "prize": "",
                "tags": tags,
                "difficulty": "beginner",
                "type": "hackathon",
                "is_closed": event.get("status", "") == "ended",
                "image_url": event.get("backgroundUrl") or "",
            })

        return items

    def _parse_iso_date(self, date_str: str) -> str | None:
        """Parse ISO date string to YYYY-MM-DD."""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None
