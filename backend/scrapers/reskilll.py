import json
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class ReskilllScraper(GenericScraper):
    platform_name = "Reskilll"
    source_key = "reskilll"
    verticals = ["hackathon"]
    BASE_URL = "https://reskilll.com"
    DISCOVER_URL = "https://reskilll.com/discover"
    MAX_PAGES = 5

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"Reskilll stage: fetching {self.DISCOVER_URL}")
        response = client.get(self.DISCOVER_URL)
        if not response.is_success:
            logger.warning(f"Reskilll request failed with status {response.status_code}")
            return []

        items = self._extract_from_rsc_payload(response.text)
        if items:
            logger.info(f"Reskilll stage: extracted {len(items)} items from RSC payload")
            self._log_sample_links(items)
            return items

        logger.info("Reskilll: no embedded data found, trying Playwright fallback")
        return self._with_playwright(self.scrape_playwright)

    def scrape_playwright(self, page) -> list[dict]:
        logger.info("Reskilll Playwright: navigating to discover page")
        page.goto(self.DISCOVER_URL, wait_until="networkidle")
        html = page.content()
        items = self._extract_from_rsc_payload(html)
        if items:
            return items

        items = self._extract_from_dom(page)
        logger.info(f"Reskilll Playwright: extracted {len(items)} items from DOM")
        self._log_sample_links(items)
        return items

    def _extract_from_rsc_payload(self, html: str) -> list[dict]:
        raw_data = self._extract_initial_data_array(html)
        if not raw_data:
            logger.info("Reskilll: initialData array not found in HTML")
            return []

        try:
            events = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.warning(f"Reskilll: failed to parse initialData JSON: {e}")
            return []

        now = datetime.now(timezone.utc)
        result = []

        for ev in events:
            if not isinstance(ev, dict):
                continue

            event_type = (ev.get("type") or "").strip()
            if event_type and event_type.lower() != "hackathon":
                continue

            deadline = ev.get("deadline", "")
            deadline_dt = self._parse_deadline(deadline)
            if deadline_dt and deadline_dt < now:
                continue

            title = (ev.get("title") or "").strip()
            if not title:
                continue

            slug = ev.get("slug") or ev.get("id", "")

            items = self._build_items(ev, title, slug, deadline_dt)
            result.extend(items)

        return result

    def _extract_initial_data_array(self, html: str) -> Optional[str]:
        idx = html.find("initialData")
        if idx == -1:
            return None

        start = html.find("[", idx)
        if start == -1:
            return None

        depth = 0
        in_string = False
        for i in range(start, len(html)):
            c = html[i]
            if c == "\\":
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    raw = html[start : i + 1]
                    raw = raw.replace('\\"', '"')
                    raw = raw.replace('\\n', ' ')
                    raw = raw.replace('\\t', ' ')
                    raw = raw.replace('\u0026amp;', '&')
                    raw = raw.replace('\u0026', '&')
                    raw = raw.replace('\u003c', '<')
                    raw = raw.replace('\u003e', '>')
                    raw = raw.replace('\u0027', "'")
                    return raw
        return None

    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        if not deadline_str or deadline_str == "$undefined":
            return None
        try:
            dt = datetime.strptime(deadline_str.strip(), "%b %d, %Y")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        try:
            dt = datetime.strptime(deadline_str.strip(), "%B %d, %Y")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            return dt
        except (ValueError, TypeError):
            pass
        return None

    def _build_items(self, ev: dict, title: str, slug: str,
                     deadline_dt: Optional[datetime]) -> list[dict]:
        organizer = (ev.get("organizer") or "").strip()
        location = (ev.get("location") or "").strip()
        mode = (ev.get("mode") or "").strip()

        tags_raw = ev.get("tags") or []
        if not isinstance(tags_raw, list):
            tags_raw = []
        tags = [t for t in tags_raw if isinstance(t, str) and t]

        if mode and mode.lower() not in [t.lower() for t in tags]:
            tags.append(mode.lower())

        if location:
            tags.append(location)

        link = f"https://{slug}" if "." in slug else f"https://reskilll.com/hack/{slug}"

        image_url = ev.get("coverImage") or ""
        prize_raw = ev.get("prize") or ""

        description = ev.get("description") or ev.get("tagline") or ""
        if not description:
            description = f"{title} is a Reskilll hackathon in {location or mode or 'India'}."

        is_closed = False
        if deadline_dt:
            is_closed = deadline_dt < datetime.now(timezone.utc)

        difficulty = self._infer_difficulty(tags)

        return [{
            "title": title,
            "organizer": organizer or "Reskilll",
            "start_date": None,
            "end_date": None,
            "date": deadline_dt.strftime("%Y-%m-%d") if deadline_dt else "",
            "location": location or mode or "",
            "link": link,
            "source_platform": "Reskilll",
            "image_url": image_url,
            "description": description,
            "prize": "",
            "tags": tags,
            "difficulty": difficulty,
            "is_closed": is_closed,
            "type": "hackathon",
        }]

    def _extract_from_dom(self, page) -> list[dict]:
        items = []
        now = datetime.now(timezone.utc)

        for page_num in range(1, self.MAX_PAGES + 1):
            if page_num > 1:
                page.goto(f"{self.DISCOVER_URL}?page={page_num}", wait_until="networkidle")

            cards = page.query_selector_all('[class*="hackathon-card"], [class*="event-card"], [class*="listing-card"], a[href*="reskilll.com/hack"]')
            logger.info(f"Reskilll DOM: page {page_num}, found {len(cards)} cards")

            for card in cards:
                try:
                    title_el = card.query_selector("h3, h2, [class*='title']")
                    title = title_el.inner_text().strip() if title_el else ""

                    if not title:
                        continue

                    link_el = card.query_selector("a[href]")
                    link = link_el.get_attribute("href") if link_el else ""

                    if link and not link.startswith("http"):
                        link = f"https://reskilll.com{link}"

                    items.append({
                        "title": title,
                        "organizer": "Reskilll",
                        "start_date": None,
                        "end_date": None,
                        "date": "",
                        "location": "India",
                        "link": link,
                        "source_platform": "Reskilll",
                        "image_url": "",
                        "description": f"{title} is a Reskilll hackathon.",
                        "prize": "",
                        "tags": [],
                        "difficulty": "beginner",
                        "is_closed": False,
                        "type": "hackathon",
                    })
                except Exception:
                    continue

            has_next = page.query_selector('[aria-label="Next"], .pagination-next, [class*="next-page"]')
            if not has_next:
                break

        return items
