import logging
import json
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class MLHScraper(GenericScraper):
    """MLH scraper — hackathons from the MLH season events page.

    MLH uses Inertia.js (Laravel-based SPA). The event data is embedded
    in a script tag as an Inertia JSON payload with component='EventsListing'.
    """

    platform_name = "MLH"
    source_key = "mlh"
    verticals = ["hackathon"]
    URL = "https://www.mlh.com/events"

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"MLH stage: fetching {self.URL}")
        response = client.get(self.URL)
        if not response.is_success:
            logger.warning(f"MLH request failed with status {response.status_code}")
            return []

        data = self._extract_inertia_payload(response.text)
        if not data:
            return []

        items = self._parse_events(data)
        logger.info(f"MLH stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _extract_inertia_payload(self, html_text: str) -> dict | None:
        """Extract the Inertia.js JSON payload from a script tag.

        MLH embeds event data as: {"component":"EventsListing","props":{...}}
        inside a <script> tag.
        """
        soup = BeautifulSoup(html_text, "html.parser")
        for script in soup.find_all("script"):
            text = script.get_text() if script.string else ""
            if "EventsListing" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                try:
                    return json.loads(text[start:end])
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"MLH: failed to parse Inertia JSON: {e}")
                    return None

        logger.warning("MLH: EventsListing payload not found in any script tag")
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
            description = f"{title} is an MLH {format_type or 'hackathon'} event in {location}."

            items.append({
                "title": title,
                "organizer": "Major League Hacking",
                "start_date": self._parse_iso_date(starts_at) if starts_at else None,
                "end_date": self._parse_iso_date(ends_at) if ends_at else None,
                "date": deadline,
                "location": location,
                "link": link,
                "source_platform": "MLH",
                "description": description,
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
