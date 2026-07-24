import logging
import re
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class HackerRankScraper(GenericScraper):
    platform_name = "HackerRank"
    source_key = "hackerrank"
    verticals = ["hackathon"]
    API_URL = "https://www.hackerrank.com/rest/contests/upcoming"
    BASE_CONTEST_URL = "https://www.hackerrank.com/contests/{slug}"

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"HackerRank stage: fetching upcoming contests")
        items = self._fetch_contests(client)
        logger.info(f"HackerRank stage: total items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_contests(self, client: httpx.Client) -> list[dict]:
        try:
            response = client.get(
                self.API_URL,
                headers={"Accept": "application/json, text/plain, */*"},
            )
            if not response.is_success:
                logger.warning(f"HackerRank API request failed with status {response.status_code}")
                return []
            payload = response.json()
            items = self._parse_items(payload)
            total = payload.get("total", 0)
            logger.info(f"HackerRank: {len(items)} upcoming out of {total} total contests")
            return items
        except Exception as exc:
            logger.warning(f"HackerRank API fetch failed: {exc}")
            return []

    def _parse_items(self, payload: dict) -> list[dict]:
        items: list[dict] = []
        models = payload.get("models", [])
        now = datetime.now(timezone.utc)

        for contest in models:
            if not isinstance(contest, dict):
                continue

            if contest.get("ended", False):
                continue

            title = (contest.get("name") or "").strip()
            if not title:
                continue

            slug = contest.get("slug") or ""
            link = self.BASE_CONTEST_URL.format(slug=slug) if slug else ""

            start_date = self._parse_iso_date(contest.get("get_starttimeiso"))
            end_date = self._parse_iso_date(contest.get("get_endtimeiso"))

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if end_dt < now:
                        continue
                except ValueError:
                    pass

            organizer = contest.get("organization_name") or "HackerRank"
            description = contest.get("description") or ""
            if description:
                description = re.sub(r"<[^>]+>", "", description).strip()

            track = contest.get("track")
            track_name = ""
            if isinstance(track, dict):
                track_name = track.get("name", "")

            tags = [track_name.lower()] if track_name else []

            items.append({
                "title": title,
                "organizer": organizer,
                "start_date": start_date,
                "end_date": end_date,
                "date": end_date or "",
                "location": "Online",
                "link": link,
                "source_platform": "HackerRank",
                "description": description,
                "prize": "",
                "tags": tags,
                "difficulty": "beginner",
                "type": "hackathon",
                "is_closed": False,
                "image_url": "",
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
