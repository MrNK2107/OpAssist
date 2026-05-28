import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class NaukriScraper(GenericScraper):
    """Naukri scraper — fresher/entry-level tech jobs from naukri.com.

    Scrapes HTML listing pages. Naukri has moderate anti-bot protection
    but works with proper headers. If blocked, returns empty gracefully.
    """

    platform_name = "Naukri"
    BASE_URL = "https://www.naukri.com"
    LISTING_URLS = [
        f"{BASE_URL}/fresher-jobs",
        f"{BASE_URL}/jobs-in-india?experience=0",
    ]
    MAX_PAGES = 2

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        # Add Naukri-specific headers to reduce blocking
        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.naukri.com/",
        })

        for base_url in self.LISTING_URLS:
            items = self._fetch_listings(client, base_url)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)

        logger.info(f"Naukri: {len(all_items)} total items")
        return all_items

    def _fetch_listings(self, client: httpx.Client, base_url: str) -> list[dict]:
        """Fetch and parse listing pages."""
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}/{page}"
            logger.info(f"Naukri: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    logger.warning("Naukri: blocked (403). Skipping remaining pages.")
                    break
                if not response.is_success:
                    logger.warning(f"Naukri page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                all_items.extend(items)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"Naukri page {page} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        """Extract job data from a Naukri listing page."""
        soup = BeautifulSoup(html_text, "html.parser")
        # Naukri uses various card selectors — try common ones
        cards = soup.select("div.srp-jobtuple-wrapper, article.jobTuple, div.row1")
        if not cards:
            # Fallback: try data attribute
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
        """Parse a single job card."""
        # Title — try multiple selectors
        title_el = card.select_one("a.title, a[href*='/job-listings-'], h2 a, .jobTupleHeader a")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # Link
        href = title_el.get("href", "") if title_el else ""
        if not href:
            link_el = card.select_one("a[href*='naukri.com']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Company
        company_el = card.select_one("a.compName, .companyInfo a, span.comp-dtls-wrap a")
        company = company_el.get_text(strip=True) if company_el else ""

        # Location
        location_el = card.select_one("span.locWdth, .locWdth, .location span")
        location = location_el.get_text(strip=True) if location_el else ""

        # Experience
        experience_el = card.select_one("span.expwdth, .expwdth, .experience span")
        experience = experience_el.get_text(strip=True) if experience_el else ""

        # Salary
        salary_el = card.select_one("span.salary, .salary, .sal span")
        salary = salary_el.get_text(strip=True) if salary_el else ""

        # Description/snippet
        desc_el = card.select_one("span.job-desc, .job-description, .jobTupleFooter")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        # Skills/tags
        tags = [s.get_text(strip=True) for s in card.select("ul.tags li, .tag-gt, .skill-tags span") if s.get_text(strip=True)]

        # Posted date
        posted_el = card.select_one("span.date, .jobTupleFooter span, .days")
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        deadline = self._infer_deadline(posted_text)

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": "",
            "is_closed": False,
        }

    def _infer_deadline(self, posted_text: str) -> str:
        """Infer deadline from 'posted X days ago' text."""
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE)
        if not match:
            if "today" in posted_text.lower() or "just now" in posted_text.lower():
                deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(days=30)
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
        deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
