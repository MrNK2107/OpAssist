import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class NaukriScraper(GenericScraper):
    """Naukri scraper — fresher/entry-level tech jobs from naukri.com.

    Uses httpx by default; falls back to Playwright stealth mode when
    Akamai CDN blocks the httpx request (403).
    """

    platform_name = "Naukri"
    source_key = "naukri"
    verticals = ["job"]
    requires_playwright = True
    BASE_URL = "https://www.naukri.com"
    LISTING_URLS = [
        f"{BASE_URL}/fresher-jobs",
        f"{BASE_URL}/jobs-in-india?experience=0",
    ]
    LATERAL_URLS = [
        f"{BASE_URL}/senior-software-engineer-jobs",
        f"{BASE_URL}/technical-lead-jobs",
        f"{BASE_URL}/engineering-manager-jobs",
        f"{BASE_URL}/jobs-in-india?experience=2",
        f"{BASE_URL}/jobs-in-india?experience=5",
        f"{BASE_URL}/jobs-in-india?experience=8",
    ]
    MAX_PAGES = 3

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, client: httpx.Client) -> list[dict]:
        """Attempt httpx first; on 403 fall back to Playwright stealth."""
        all_items: list[dict] = []
        seen_urls: set[str] = set()
        blocked = False

        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.naukri.com/",
        })

        for base_url in self.LISTING_URLS + self.LATERAL_URLS:
            try:
                items = self._fetch_listings(client, base_url)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
            except ScrapeBlockedError:
                blocked = True
                break

        if blocked or not all_items:
            if blocked:
                logger.info("Naukri: httpx blocked (403), falling back to Playwright")
            else:
                logger.info("Naukri: no items from httpx, trying Playwright fallback")
            return self._with_playwright(self._playwright_scrape)

        logger.info(f"Naukri: {len(all_items)} total items")
        return all_items

    # ------------------------------------------------------------------
    # Playwright stealth fallback
    # ------------------------------------------------------------------

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Naukri (Playwright): starting stealth scrape")

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for base_url in self.LISTING_URLS + self.LATERAL_URLS:
            for page_num in range(1, self.MAX_PAGES + 1):
                url = base_url if page_num == 1 else f"{base_url}/{page_num}"
                logger.info(f"Naukri (Playwright): fetching {url}")

                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)

                    try:
                        page.wait_for_selector(
                            ".srp-jobtuple-wrapper, article.jobTuple",
                            timeout=20000,
                        )
                    except Exception:
                        logger.warning(
                            f"Naukri (Playwright): no job cards on {url}"
                        )
                        break

                    page.wait_for_timeout(2000)

                    html = page.content()
                    items = self._parse_listing_page(html)

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(
                        f"Naukri (Playwright): page {page_num} -> {len(items)} items"
                    )
                    if not items:
                        break

                except ScrapeBlockedError:
                    raise
                except Exception as e:
                    logger.warning(
                        f"Naukri (Playwright): error on page {page_num}: {e}"
                    )
                    break

        logger.info(f"Naukri (Playwright): {len(all_items)} total items")
        return all_items

    # ------------------------------------------------------------------
    # httpx fetching
    # ------------------------------------------------------------------

    def _fetch_listings(
        self, client: httpx.Client, base_url: str
    ) -> list[dict]:
        """Fetch and parse listing pages via httpx."""
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            url = base_url if page == 1 else f"{base_url}/{page}"
            logger.info(f"Naukri: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(
                        source=self.source_key, status_code=403
                    )
                if not response.is_success:
                    logger.warning(
                        f"Naukri page {page}: HTTP {response.status_code}"
                    )
                    break
                items = self._parse_listing_page(response.text)
                all_items.extend(items)
                if not items:
                    break
            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"Naukri page {page} error: {exc}")
                break

        return all_items

    # ------------------------------------------------------------------
    # HTML parsing (shared by httpx and Playwright paths)
    # ------------------------------------------------------------------

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(
            "div.srp-jobtuple-wrapper, article.jobTuple, div.row1"
        )
        if not cards:
            cards = soup.select("[data-job-id]")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Naukri: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "a.title, a[href*='/job-listings-'], h2 a, .jobTupleHeader a"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        href = title_el.get("href", "") if title_el else ""
        if not href:
            link_el = card.select_one("a[href*='naukri.com']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = (
            href
            if href.startswith("http")
            else f"{self.BASE_URL}{href}"
        )

        company_el = card.select_one(
            "a.compName, .companyInfo a, span.comp-dtls-wrap a"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "span.locWdth, .locWdth, .location span"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        experience_el = card.select_one(
            "span.expwdth, .expwdth, .experience span"
        )
        experience = (
            experience_el.get_text(strip=True) if experience_el else ""
        )

        salary_el = card.select_one("span.salary, .salary, .sal span")
        salary = salary_el.get_text(strip=True) if salary_el else ""

        desc_el = card.select_one(
            "span.job-desc, .job-description, .jobTupleFooter"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        tags = [
            s.get_text(strip=True)
            for s in card.select(
                "ul.tags li, .tag-gt, .skill-tags span"
            )
            if s.get_text(strip=True)
        ]

        posted_el = card.select_one(
            "span.date, .jobTupleFooter span, .days"
        )
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
            "prize": salary,
            "salary_currency": "INR",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "remote": "remote" in (title + location).lower() or "work from home" in (title + description).lower(),
            "date": deadline,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": "",
            "is_closed": False,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_experience(exp_text: str) -> tuple[int | None, int | None]:
        if not exp_text:
            return None, None
        match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)", exp_text)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"(\d+)\s*\+?\s*(?:yr|year|y)", exp_text)
        if match:
            val = int(match.group(1))
            return val, val + 2
        return None, None

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        match = re.search(
            r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE
        )
        if not match:
            if "today" in posted_text.lower() or "just now" in posted_text.lower():
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
