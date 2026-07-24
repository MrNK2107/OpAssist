import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class FounditScraper(GenericScraper):
    platform_name = "Foundit"
    source_key = "foundit"
    verticals = ["job"]
    requires_playwright = True
    BASE_URL = "https://www.foundit.in"
    MAX_PAGES = 3
    SEARCH_QUERIES = [
        "fresher",
        "entry-level",
        "graduate",
    ]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"{self.BASE_URL}/",
            "User-Agent": "Mozilla/5.0",
        })

        blocked = False
        for query in self.SEARCH_QUERIES:
            try:
                items = self._fetch_query(client, query, seen_urls)
                all_items.extend(items)
            except Exception:
                blocked = True
                break

        if blocked or not all_items:
            logger.info("Foundit: httpx blocked or empty, falling back to Playwright")
            return self._with_playwright(self._playwright_scrape)

        self._log_sample_links(all_items)
        logger.info(f"Foundit: {len(all_items)} total jobs found")
        return all_items

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Foundit (Playwright): starting stealth scrape")
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
        })

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.SEARCH_QUERIES:
            for page_num in range(1, self.MAX_PAGES + 1):
                if page_num == 1:
                    url = f"{self.BASE_URL}/search/{query}-jobs"
                else:
                    url = f"{self.BASE_URL}/search/{query}-jobs-{page_num}"
                logger.info(f"Foundit (Playwright): fetching {url}")
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    page.wait_for_timeout(3000)
                    html = page.content()
                    items = self._parse_listing_page(html)
                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)
                    if not items:
                        break
                    logger.info(f"Foundit (Playwright): {url} -> {len(items)} items")
                except Exception as e:
                    logger.warning(f"Foundit (Playwright): {url} error: {e}")
                    break
            if all_items:
                break

        logger.info(f"Foundit (Playwright): {len(all_items)} total items")
        return all_items

    def _fetch_query(
        self, client: httpx.Client, query: str, seen_urls: set[str]
    ) -> list[dict]:
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            if page == 1:
                url = f"{self.BASE_URL}/search/{query}-jobs"
            else:
                url = f"{self.BASE_URL}/search/{query}-jobs-{page}"

            logger.info(f"Foundit: fetching {url}")
            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(source=self.source_key, status_code=403)
                if not response.is_success:
                    logger.warning(
                        f"Foundit {url}: HTTP {response.status_code}"
                    )
                    break
                items = self._parse_listing_page(response.text)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                if not items:
                    break
            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"Foundit {url} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.jobCardWrapper")
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Foundit: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one("h2.jobCardTitle")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            return None

        link_el = card.select_one("h2.jobCardTitle a")
        link = ""
        if link_el:
            href = link_el.get("href", "")
            link = href if href.startswith("http") else f"{self.BASE_URL}{href}"
        if not link:
            return None

        company_el = card.select_one(".jobCardCompany span, .jobCardCompany a")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".jobCardLocation span")
        location = location_el.get_text(strip=True) if location_el else ""

        experience_el = card.select_one("div.jobCardExperience label")
        experience = (
            experience_el.get_text(strip=True) if experience_el else ""
        )

        tags = self._extract_tags(card)

        description = card.get_text(" ", strip=True)[:500]

        salary = ""

        posted_el = card.select_one("div.jobCardEarlyApplicant, span.text-xxs")
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        deadline = self._infer_deadline(posted_text)
        exp_min, exp_max = self._parse_experience(experience)

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "experience": experience,
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "prize": salary,
            "date": deadline,
            "tags": tags,
            "difficulty": self._resolve_experience_level(exp_min, exp_max, title, tags),
            "image_url": "",
            "is_closed": False,
        }

    @staticmethod
    def _parse_experience(experience: str) -> tuple[int | None, int | None]:
        if not experience:
            return None, None
        match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", experience)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"(\d+)\s*\+?\s*(?:year|yr)", experience, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            return value, value + 2
        if re.search(r"fresher|0\s*(?:year|yr)", experience, re.IGNORECASE):
            return 0, 1
        return None, None

    def _extract_tags(self, card) -> list[str]:
        for label in card.find_all(string=re.compile(r"^\s*Skills:\s*$", re.IGNORECASE)):
            container = label.find_parent()
            if not container:
                continue
            wrapper = container.find_parent()
            if not wrapper:
                continue
            raw = wrapper.get_text(" ", strip=True)
            raw = re.sub(r"^\s*Skills:\s*", "", raw, flags=re.IGNORECASE)
            tags = [
                re.sub(r"\s+", " ", part).strip(" ,")
                for part in raw.split(",")
            ]
            return [tag for tag in tags if tag and len(tag) <= 60][:20]
        return []

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")
        match = re.search(
            r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE
        )
        if not match:
            if "today" in posted_text.lower() or "just now" in posted_text.lower() or "early" in posted_text.lower():
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            return ""
        count = int(match.group(1))
        unit = match.group(2).lower()
        if "month" in unit:
            days_ago = count * 30
        elif "week" in unit:
            days_ago = count * 7
        else:
            days_ago = count
        days_remaining = max(0, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
