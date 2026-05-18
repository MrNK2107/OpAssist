import logging
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class HackerEarthScraper(GenericScraper):
    """HackerEarth scraper — challenges, hackathons, hiring."""

    platform_name = "HackerEarth"
    COMPETE_URL = "https://www.hackerearth.com/api/community/challenges/compete/"
    HIRING_URL = "https://www.hackerearth.com/api/community/challenges/hiring/"

    def scrape(self, client: httpx.Client) -> list[dict]:
        items: list[dict] = []

        logger.info(f"HackerEarth stage: fetching compete challenges")
        items.extend(self._fetch_endpoint(client, self.COMPETE_URL))

        logger.info(f"HackerEarth stage: fetching hiring challenges")
        items.extend(self._fetch_endpoint(client, self.HIRING_URL))

        logger.info(f"HackerEarth stage: total items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_endpoint(self, client: httpx.Client, url: str) -> list[dict]:
        try:
            response = client.get(url)
            if not response.is_success:
                logger.warning(f"HackerEarth API request failed with status {response.status_code}")
                return []
            payload = response.json()
            data = payload.get("data", [])
            return self._parse_items(data)
        except Exception as exc:
            logger.warning(f"HackerEarth API fetch failed: {exc}")
            return []

    def _parse_items(self, data: list[dict]) -> list[dict]:
        items = []
        now = datetime.now(timezone.utc)

        for event in data:
            end_str = event.get("end")
            deadline = self._parse_iso_date(end_str)

            # Skip events with past deadlines
            if deadline:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if deadline_dt < now:
                    continue

            title = (event.get("title") or "").strip()
            if not title:
                continue

            event_url = event.get("url", "")
            link = event_url if event_url.startswith("http") else f"https://www.hackerearth.com{event_url}" if event_url else ""

            event_type = event.get("type", "")
            tags = [event_type.lower()] if event_type else []

            # Determine opportunity type
            if event_type == "Hiring":
                opp_type = "internship"
            elif event_type == "Hackathon":
                opp_type = "hackathon"
            else:
                opp_type = "hackathon"

            company = event.get("company_name", "")
            organizer = company if company else "HackerEarth"

            image_url = event.get("listing_image") or event.get("image_url") or ""

            items.append({
                "title": title,
                "organizer": organizer,
                "start_date": self._parse_iso_date(event.get("start")),
                "end_date": deadline,
                "date": deadline or "",
                "location": "Online",
                "link": link,
                "source_platform": "HackerEarth",
                "description": "",
                "prize": "",
                "tags": tags,
                "difficulty": self._infer_difficulty(tags),
                "type": opp_type,
                "is_closed": False,
                "image_url": image_url,
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
