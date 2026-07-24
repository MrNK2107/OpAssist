import logging
from datetime import datetime, timezone
from typing import Optional
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class DoraHacksScraper(GenericScraper):
    platform_name = "DoraHacks"
    source_key = "dorahacks"
    verticals = ["hackathon"]
    API_URL = "https://dorahacks.io/api/hackathon/"
    MAX_PAGES = 5
    PAGE_SIZE = 50

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"DoraHacks stage: calling API {self.API_URL}")
        items = self._fetch_paginated(client)
        logger.info(f"DoraHacks stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_paginated(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            logger.info(f"DoraHacks: fetching page {page}")
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
                params={"page": page, "page_size": self.PAGE_SIZE},
                headers={
                    "Referer": "https://dorahacks.io/hackathon",
                    "Origin": "https://dorahacks.io",
                },
            )
            if not response.is_success:
                logger.warning(f"DoraHacks API request failed with status {response.status_code}")
                return [], False
            payload = response.json()
            results = payload.get("results", [])
            items = self._parse_items(results)
            # Check if there are more pages
            next_url = payload.get("next")
            has_more = bool(next_url) and len(results) > 0
            return items, has_more
        except Exception as exc:
            logger.warning(f"DoraHacks API fetch failed: {exc}")
            return [], False

    def _parse_items(self, results: list[dict]) -> list[dict]:
        items: list[dict] = []
        now = datetime.now(timezone.utc)

        for h in results:
            if not isinstance(h, dict):
                continue

            title = (h.get("title") or "").strip()
            uname = (h.get("uname") or "").strip()
            hid = h.get("id")
            if not title:
                continue

            # Build URL
            slug = uname or str(hid) if hid else ""
            link = f"https://dorahacks.io/hackathon/{slug}" if slug else ""

            # Parse timestamps (all are unix seconds)
            start_time = self._parse_timestamp(h.get("start_time"))
            end_time = self._parse_timestamp(h.get("end_time"))
            deadline = self._parse_timestamp(h.get("pre_register_time"))

            # Skip if end_time has already passed
            if end_time:
                if end_time < now:
                    continue

            # Location
            location = self._build_location(h)

            # Organizer
            org = h.get("organization") or {}
            organizer = (org.get("name") or "").strip() if isinstance(org, dict) else ""

            # Tags from field and ecosystem
            tags = self._build_tags(h)

            # Prize
            prize = self._format_prize(h)

            # Description (clean markdown)
            description = (h.get("description") or "").strip()

            # Status
            status = h.get("status")
            is_closed = status in (2, 3) or (end_time and end_time < now)

            items.append({
                "title": title,
                "organizer": organizer,
                "start_date": start_time.strftime("%Y-%m-%d") if start_time else None,
                "end_date": end_time.strftime("%Y-%m-%d") if end_time else None,
                "date": deadline.strftime("%Y-%m-%d") if deadline else (end_time.strftime("%Y-%m-%d") if end_time else ""),
                "location": location,
                "link": link,
                "source_platform": "DoraHacks",
                "image_url": h.get("image_url") or "",
                "description": description[:1000] if description else "",
                "prize": prize,
                "tags": tags,
                "difficulty": self._infer_difficulty(tags),
                "is_closed": is_closed,
                "type": "hackathon",
            })

        return items

    def _build_location(self, h: dict) -> str:
        participation = (h.get("participation_form") or "").strip()
        if participation:
            return participation

        venue_name = (h.get("venue_name") or "").strip()
        venue_address = (h.get("venue_address") or "").strip()
        if venue_name or venue_address:
            return ", ".join(p for p in [venue_name, venue_address] if p)

        return "Virtual"

    def _build_tags(self, h: dict) -> list[str]:
        tags: list[str] = []

        field = (h.get("field") or "").strip()
        if field:
            for t in field.split(","):
                t = t.strip()
                if t:
                    tags.append(t)

        ecosystem = (h.get("ecosystem") or "").strip()
        if ecosystem:
            for t in ecosystem.split(","):
                t = t.strip()
                if t and t not in tags:
                    tags.append(t)

        return tags

    def _format_prize(self, h: dict) -> str:
        amount = h.get("bonus_price")
        token = (h.get("token") or "USD").strip()
        if amount:
            try:
                val = float(amount)
                if val > 0:
                    prize = f"{token} {val:,.0f}" if val >= 1000 else f"{token} {val:.2f}"
                    return self._sanitize_prize(prize)
            except (ValueError, TypeError):
                pass
        return ""

    @staticmethod
    def _parse_timestamp(ts) -> Optional[datetime]:
        if ts is None or ts == 0:
            return None
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except (ValueError, OSError):
            return None
