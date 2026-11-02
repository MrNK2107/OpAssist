import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class GlassdoorInternshipsScraper(GenericScraper):
    """Glassdoor Internships scraper — internship listings from glassdoor.co.in.

    Glassdoor blocks httpx aggressively (Akamai CDN), so the primary scraping
    path uses Playwright stealth mode. httpx is attempted only as a best-effort
    first pass.
    """

    platform_name = "GlassdoorInternships"
    source_key = "glassdoor_internships"
    verticals = ["internship"]
    requires_playwright = True

    BASE_URL = "https://www.glassdoor.co.in"
    LISTING_URL = f"{BASE_URL}/Internship/jobs-SRCH_KO0,10.htm"
    ALTERNATE_URL = f"{BASE_URL}/internship-jobs-SRCH_KO0,10.htm"
    MAX_PAGES = 3

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, client: httpx.Client) -> list[dict]:
        """Attempt httpx first; fall back to Playwright on 403."""
        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.glassdoor.co.in/",
        })

        try:
            items = self._fetch_listings_httpx(client)
            if items:
                logger.info(f"Glassdoor: {len(items)} items via httpx")
                return items
        except ScrapeBlockedError:
            logger.info("Glassdoor: httpx blocked (403), falling back to Playwright")

        return self._with_playwright(self._playwright_scrape)

    # ------------------------------------------------------------------
    # httpx path (best-effort; usually blocked)
    # ------------------------------------------------------------------

    def _fetch_listings_httpx(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self.LISTING_URL if page == 1 else f"{self.LISTING_URL}?p={page}"
            logger.info(f"Glassdoor (httpx): page {page} -> {url}")

            response = client.get(url, timeout=30)
            if response.status_code == 403:
                raise ScrapeBlockedError(source=self.source_key, status_code=403)
            if not response.is_success:
                logger.warning(f"Glassdoor page {page}: HTTP {response.status_code}")
                break

            items = self._parse_listing_page(response.text)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)

            if not items:
                break

        return all_items

    # ------------------------------------------------------------------
    # Playwright stealth path (primary)
    # ------------------------------------------------------------------

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Glassdoor (Playwright): starting stealth scrape")

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            window.chrome = { runtime: {} };
        """)

        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        all_items: list[dict] = []
        seen_urls: set[str] = set()
        urls_to_try = [self.LISTING_URL, self.ALTERNATE_URL]

        for base_url in urls_to_try:
            for page_num in range(1, self.MAX_PAGES + 1):
                url = base_url if page_num == 1 else f"{base_url}?p={page_num}"
                logger.info(f"Glassdoor (Playwright): fetching {url}")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(5000)

                    card_selectors = [
                        "li[data-test='job-list-item']",
                        "div[id*='JobCard']",
                        "article[data-test*='job']",
                        "div[class*='jobListing']",
                        "div[class*='jobCard']",
                        "li[class*='job']",
                        "div[data-testid='job-card']",
                        "div[class*='job-container']",
                        ".react-job-listing",
                        "[data-job-id]",
                    ]

                    found_cards = False
                    for selector in card_selectors:
                        try:
                            page.wait_for_selector(selector, timeout=8000)
                            found_cards = True
                            break
                        except Exception:
                            continue

                    if not found_cards:
                        logger.warning(f"Glassdoor (Playwright): no job cards on {url}")
                        if base_url == urls_to_try[-1]:
                            break
                        continue

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)

                    html = page.content()
                    items = self._parse_listing_page(html)

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(f"Glassdoor (Playwright): page {page_num} -> {len(items)} items")

                    if not items:
                        break

                except ScrapeBlockedError:
                    raise
                except Exception as e:
                    logger.warning(f"Glassdoor (Playwright): error on page {page_num}: {e}")
                    break

        logger.info(f"Glassdoor (Playwright): {len(all_items)} total items")
        return all_items

    # ------------------------------------------------------------------
    # HTML parsing (shared by both paths)
    # ------------------------------------------------------------------

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(
            "li[data-test='job-list-item'], "
            "div[id*='JobCard'], "
            "article[data-test*='job'], "
            "div.jobContainer, "
            "div[class*='jobListing'], "
            "div[class*='jobCard'], "
            "li[class*='job'], "
            "div[data-testid='job-card'], "
            ".react-job-listing, "
            "[data-job-id]"
        )
        if not cards:
            cards = soup.select("[data-job-id], [data-id*='job'], div[class*='listing']")
        if not cards:
            cards = soup.select("div[class*='container'] > div[class*='row'] > div[class*='col']")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Glassdoor: failed to parse card: {exc}")

        return self._dedupe_by_link(items)

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "a.jobLink, "
            "a[data-test='job-link'], "
            "a[class*='jobTitle'], "
            "a[href*='/partner/jobListing'], "
            "a[href*='job-listing'], "
            "a[class*='title'], "
            "h2 a, h3 a, "
            "[data-test='job-title'], "
            "[class*='job-title'], "
            "a[href*='/job']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title_el = card.select_one("a[href*='job-listing']")
            title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title_el = card.select_one("a[class*='job'], a[class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        href = title_el.get("href", "") if title_el else ""
        if not href:
            link_el = card.select_one("a[href*='/job-listing'], a[href*='/job'], a[href*='partner']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        company_el = card.select_one(
            "div.employerName, "
            "span[data-test='employer-name'], "
            "div[class*='employer'], "
            "span[class*='company'], "
            "[data-test='employer-name'], "
            "div[class*='company']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "span[data-test='location'], "
            "div[class*='location'], "
            "span[class*='loc'], "
            "[data-test='location'], "
            "span[class*='location']"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        salary_el = card.select_one(
            "span[data-test='detail-salary'], "
            "span[class*='salary'], "
            "span[class*='est'], "
            "[data-test='detail-salary'], "
            "span[class*='pay']"
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        desc_el = card.select_one(
            "div[class*='jobDescription'], "
            "span[class*='desc'], "
            "div[class*='snippet'], "
            "[class*='description'], "
            "[class*='job-desc']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        posted_el = card.select_one(
            "span[data-test='age'], "
            "span[class*='posted'], "
            "span[class*='age'], "
            "div[class*='time'], "
            "[data-test='age'], "
            "span[class*='date']"
        )
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        deadline = self._infer_deadline(posted_text)

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline,
            "tags": [],
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scroll_for_lazy_load(page) -> None:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""

        text = posted_text.lower().strip()

        if text in ("24h", "24hr", "1d", "1 day ago", "today"):
            deadline = datetime.now(timezone.utc) + timedelta(days=29)
            return deadline.strftime("%Y-%m-%d")

        if "30d+" in text or "30+" in text or "30 days" in text or "month" in text:
            deadline = datetime.now(timezone.utc) + timedelta(days=1)
            return deadline.strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*(d|day|hr|h|week|wk|month|mon)", text)
        if not match:
            if "just now" in text or "moments" in text:
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            return ""

        count = int(match.group(1))
        unit = match.group(2)

        if unit in ("month", "mon"):
            days_ago = count * 30
        elif unit in ("week", "wk"):
            days_ago = count * 7
        elif unit in ("day", "d"):
            days_ago = count
        else:
            days_ago = count

        days_remaining = max(0, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
