import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)

API_URL = "https://www.codechef.com/api/list/contests/all"


class CodeChefScraper(GenericScraper):
    platform_name = "CodeChef"
    source_key = "codechef"
    verticals = ["hackathon"]

    def scrape(self, client: httpx.Client) -> list[dict]:
        try:
            response = client.get(API_URL)
            if not response.is_success:
                logger.warning(f"CodeChef API returned {response.status_code}")
                return []
            payload = response.json()
        except Exception as exc:
            logger.warning(f"CodeChef API fetch failed: {exc}")
            return []

        if payload.get("status") != "success":
            logger.warning("CodeChef API returned non-success status")
            return []

        raw_contests = payload.get("future_contests", [])
        if not raw_contests:
            logger.info("CodeChef: no future contests found")
            return []

        items = self._parse_contests(raw_contests)
        logger.info(f"CodeChef: parsed {len(items)} future contests")
        self._log_sample_links(items)
        return items

    def _parse_contests(self, contests: list[dict]) -> list[dict]:
        items: list[dict] = []
        now = datetime.now(timezone.utc)

        for contest in contests:
            end_date = self._parse_iso(contest.get("contest_end_date_iso"))
            if end_date and end_date < now:
                continue

            code = contest.get("contest_code", "")
            name = (contest.get("contest_name") or "").strip()
            if not name or not code:
                continue

            start_date = self._parse_iso(contest.get("contest_start_date_iso"))

            tags = self._extract_tags(contest)

            items.append({
                "title": name,
                "organizer": "CodeChef",
                "start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
                "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
                "date": start_date.strftime("%Y-%m-%d") if start_date else (end_date.strftime("%Y-%m-%d") if end_date else ""),
                "location": "Online",
                "link": f"https://www.codechef.com/{code}",
                "source_platform": "CodeChef",
                "description": f"CodeChef contest: {name}",
                "prize": "",
                "tags": tags,
                "difficulty": self._infer_difficulty(tags),
                "type": "hackathon",
                "is_closed": False,
                "image_url": "",
            })

        return items

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_tags(contest: dict[str, Any]) -> list[str]:
        tags: list[str] = []
        name = (contest.get("contest_name") or "").lower()

        if "rated" in name:
            tags.append("rated")
        if "starters" in name:
            tags.append("starters")
        if "challenge" in name:
            tags.append("challenge")
        if "dsa" in name:
            tags.append("dsa")
        if "munch" in name:
            tags.append("dsa-practice")
        if "weekend" in name:
            tags.append("weekend-dev-challenge")

        return tags
