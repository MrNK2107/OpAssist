import logging
import re
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class DevpostScraper(GenericScraper):
    """Devpost scraper — hackathons from devpost.com."""

    platform_name = "Devpost"
    API_URL = "https://devpost.com/api/hackathons"
    MAX_PAGES = 5  # Fetch up to 5 pages (45 hackathons at 9/page)

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"Devpost stage: calling API {self.API_URL}")
        items = self._fetch_paginated(client)
        logger.info(f"Devpost stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_paginated(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            logger.info(f"Devpost: fetching page {page}")
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
            response = client.get(self.API_URL, params={"page": page})
            if not response.is_success:
                logger.warning(f"Devpost API request failed with status {response.status_code}")
                return [], False
            payload = response.json()
            return self._parse_api_payload(payload), self._has_more(payload, page)
        except Exception as exc:
            logger.warning(f"Devpost API fetch failed: {exc}")
            return [], False

    def _has_more(self, payload: dict, current_page: int) -> bool:
        meta = payload.get("meta", {})
        total = meta.get("total_count", 0)
        per_page = meta.get("per_page", 9)
        return current_page * per_page < total

    def _parse_api_payload(self, payload: dict) -> list[dict]:
        items: list[dict] = []
        hackathons = payload.get("hackathons", [])
        now = datetime.now(timezone.utc)

        for h in hackathons:
            if not isinstance(h, dict):
                continue

            title = (h.get("title") or "").strip()
            if not title:
                continue

            url = h.get("url") or ""
            if not url:
                continue

            start_date, end_date, deadline = self._parse_dates(h.get("submission_period_dates", ""))

            # Skip expired hackathons — deadline must be in the future
            if deadline:
                try:
                    deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if deadline_dt < now:
                        continue
                except ValueError:
                    pass

            location_obj = h.get("displayed_location") or {}
            location = location_obj.get("location") or "Online"

            prize_raw = self._strip_html(h.get("prize_amount") or "")
            prize = "" if prize_raw in ("$0", "0", "$0.00") else prize_raw

            themes = [t.get("name", "") for t in (h.get("themes") or []) if isinstance(t, dict)]
            tags = [t for t in themes if t]

            difficulty = self._infer_difficulty(tags)
            is_open = (h.get("open_state") or "").lower() == "open"

            # Build description from available fields
            description_parts = []
            if h.get("tagline"):
                description_parts.append(h["tagline"])
            if h.get("organization_name"):
                description_parts.append(f"Hosted by {h['organization_name']}")
            if h.get("invite_only"):
                description_parts.append("Invite only")

            items.append({
                "title": title,
                "organizer": h.get("organization_name") or "",
                "start_date": start_date,
                "end_date": end_date,
                "date": deadline,
                "location": location,
                "link": url,
                "source_platform": "Devpost",
                "description": " | ".join(description_parts) if description_parts else "",
                "prize": prize,
                "tags": tags,
                "difficulty": difficulty,
                "type": "hackathon",
                "is_closed": not is_open,
                "image_url": h.get("thumbnail_url") or "",
            })

        return items

    def _parse_dates(self, date_str: str) -> tuple[str | None, str | None, str | None]:
        """Parse submission_period_dates into (start_date, end_date, deadline).

        Formats: "May 05 - Jun 11, 2026" or "May 11 - 28, 2026" or "May 01, 2026"
        Returns (start_date, end_date, deadline) where deadline = end_date.
        """
        if not date_str:
            return None, None, None

        parts = date_str.split(" - ")
        if len(parts) < 2:
            # Single date like "May 01, 2026"
            parsed = self._try_parse_date(date_str.strip())
            return parsed, parsed, parsed

        start_part = parts[0].strip()
        end_part = parts[-1].strip()

        # Parse end date
        end_date = self._try_parse_date(end_part)
        if not end_date:
            # End part is just "DD, YYYY" — extract month from start
            start_mon = self._extract_month(start_part)
            if start_mon:
                end_date = self._try_parse_date(f"{start_mon} {end_part}")

        # Parse start date
        start_date = self._try_parse_date(start_part)
        if not start_date and end_date:
            # Start part is just "Mon DD" — reconstruct with year from end
            year = end_date[:4]
            start_mon = self._extract_month(start_part)
            if start_mon:
                day_match = re.search(r"(\d+)", start_part)
                if day_match:
                    start_date = self._try_parse_date(f"{start_mon} {day_match.group(1)}, {year}")

        return start_date, end_date, end_date

    def _try_parse_date(self, text: str) -> str | None:
        for fmt in ["%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"]:
            try:
                dt = datetime.strptime(text.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _extract_month(self, text: str) -> str | None:
        """Extract month name from start part like 'May 11'."""
        match = re.match(r"([A-Za-z]+)\s+\d+", text.strip())
        return match.group(1) if match else None

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r"<[^>]+>", "", text).strip()

    # _infer_difficulty inherited from GenericScraper
