import logging
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class DevfolioScraper(GenericScraper):
    """Devfolio scraper — hackathons from devfolio.co."""

    platform_name = "Devfolio"
    API_URL = "https://api.devfolio.co/api/hackathons"
    MAX_PAGES = 5

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"Devfolio stage: calling API {self.API_URL}")
        items = self._fetch_paginated(client)
        logger.info(f"Devfolio stage: items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_paginated(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()
        total_pages = self.MAX_PAGES

        for page in range(1, total_pages + 1):
            logger.info(f"Devfolio: fetching page {page}")
            items, has_more, pages = self._fetch_page(client, page)

            for item in items:
                url = item.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)

            if pages and pages < total_pages:
                total_pages = pages

            if not has_more:
                break

        return all_items

    def _fetch_page(self, client: httpx.Client, page: int) -> tuple[list[dict], bool, int]:
        try:
            response = client.get(self.API_URL, params={"page": page}, timeout=30)
            if not response.is_success:
                logger.warning(f"Devfolio API request failed with status {response.status_code}")
                return [], False, 0
            payload = response.json()
            pages = payload.get("pages", 1)
            items = self._parse_api_payload(payload)
            has_more = page < pages
            return items, has_more, pages
        except Exception as exc:
            logger.warning(f"Devfolio API fetch failed: {exc}")
            return [], False, 0

    def _parse_api_payload(self, payload: dict) -> list[dict]:
        items: list[dict] = []
        hackathons = payload.get("result", [])
        now = datetime.now(timezone.utc)

        for h in hackathons:
            if not isinstance(h, dict):
                continue

            # Skip private hackathons
            if h.get("private"):
                continue

            # Only include HACKATHON type
            h_type = (h.get("type") or "").upper()
            if h_type and h_type != "HACKATHON":
                continue

            title = (h.get("name") or "").strip()
            slug = (h.get("slug") or "").strip()
            if not title or not slug:
                continue

            link = f"https://devfolio.co/hackathons/{slug}"

            # Location
            location = self._build_location(h)

            # Deadline from hackathon_setting.reg_ends_at
            settings = h.get("hackathon_setting") or {}
            deadline = self._normalize_date(settings.get("reg_ends_at"))

            # Skip expired hackathons — deadline must be in the future
            if deadline:
                try:
                    deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if deadline_dt < now:
                        continue
                except ValueError:
                    pass

            # Dates
            start_date = self._normalize_date(h.get("starts_at"))
            end_date = self._normalize_date(h.get("ends_at"))

            # Description
            description = h.get("tagline") or h.get("desc") or ""

            # Organizer
            brand = h.get("hackathon_brand") or {}
            organizer = brand.get("name") or h.get("hackathon_setting", {}).get("organizer_name", "") or ""

            # Image
            image_url = h.get("cover_img") or settings.get("logo") or ""

            # Tags from themes
            themes = h.get("themes") or []
            tags = [t.get("name", "") for t in themes if isinstance(t, dict) and t.get("name")]

            # Prize from prizes
            prize = self._format_prizes(h.get("prizes") or [])

            # Difficulty
            difficulty = self._infer_difficulty(tags)

            # Open/closed: check if registration deadline has passed
            is_closed = self._is_closed(deadline)

            items.append({
                "title": title,
                "organizer": organizer,
                "start_date": start_date,
                "end_date": end_date,
                "date": deadline,
                "location": location,
                "link": link,
                "source_platform": "Devfolio",
                "image_url": image_url,
                "description": description,
                "prize": prize,
                "tags": tags,
                "difficulty": difficulty,
                "is_closed": is_closed,
                "type": "hackathon",
            })

        return items

    def _build_location(self, h: dict) -> str:
        location = h.get("location") or ""
        if location:
            return location.strip()
        city = h.get("city") or ""
        country = h.get("country") or ""
        parts = [p for p in [city, country] if p]
        if parts:
            return ", ".join(parts)
        if h.get("is_online"):
            return "Online"
        return ""

    def _format_prizes(self, prizes: list) -> str:
        if not prizes:
            return ""
        amounts = []
        names = []
        for p in prizes:
            if not isinstance(p, dict):
                continue
            amount = p.get("amount")
            currency = p.get("currency") or ""
            name = p.get("name") or ""
            if amount:
                try:
                    val = float(amount)
                    if val > 0:
                        amounts.append((currency, val))
                except (ValueError, TypeError):
                    if name:
                        names.append(name)
            elif name:
                names.append(name)
        if amounts:
            # Show total of monetary prizes
            total = sum(a for _, a in amounts)
            currency = amounts[0][0] or "USD"
            if total >= 1000:
                return f"{currency} {total:,.0f}"
            return f"{currency} {total:.2f}"
        # Fall back to prize names (just first few)
        return ", ".join(names[:3]) if names else ""

    def _normalize_date(self, raw_date) -> str | None:
        if not raw_date:
            return None
        text = str(raw_date).strip()
        if not text:
            return None
        if "T" in text:
            text = text.split("T")[0]
        if len(text) >= 10:
            text = text[:10]
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            return None

    def _is_closed(self, deadline: str | None) -> bool:
        if not deadline:
            return False
        try:
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            return deadline_dt < datetime.now(timezone.utc)
        except ValueError:
            return False

    # _infer_difficulty inherited from GenericScraper
