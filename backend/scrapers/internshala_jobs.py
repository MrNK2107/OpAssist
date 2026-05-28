import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class InternshalaJobsScraper(GenericScraper):
    """Internshala Jobs scraper — fresher jobs from internshala.com.

    Same two-pass approach as InternshalaScraper but targeting job listings.
    """

    platform_name = "InternshalaJobs"
    BASE_URL = "https://internshala.com"
    LISTING_URLS = [
        f"{BASE_URL}/fresher-jobs",
        f"{BASE_URL}/jobs",
    ]
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for base_url in self.LISTING_URLS:
            items = self._fetch_listings(client, base_url, seen_urls)
            all_items.extend(items)

        logger.info(f"InternshalaJobs: {len(all_items)} total jobs found")
        return all_items

    def _fetch_listings(self, client: httpx.Client, base_url: str, seen_urls: set[str]) -> list[dict]:
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{base_url}/page-{page}/" if page > 1 else f"{base_url}/"
            logger.info(f"InternshalaJobs: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"InternshalaJobs page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"InternshalaJobs page {page} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.individual_internship")
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"InternshalaJobs: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        # Title
        title_el = card.select_one("h2.job-internship-name a.job-title-href")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # Link
        href = card.get("data-href", "")
        if not href:
            link_el = card.select_one('a[href*="/job/detail/"]')
            if not link_el:
                link_el = card.select_one("a.job-title-href")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Company
        company_el = card.select_one("p.company-name")
        company = company_el.get_text(strip=True) if company_el else ""

        # Location
        location_el = card.select_one(".row-1-item.locations span a")
        location = location_el.get_text(strip=True) if location_el else "India"

        # Salary
        salary_el = card.select_one("span.stipend")
        salary = salary_el.get_text(strip=True) if salary_el else ""

        # Experience
        experience = ""
        for item in card.select(".detail-row-1 .row-1-item"):
            icon = item.select_one("i")
            if icon and "ic-16-briefcase" in " ".join(icon.get("class", [])):
                experience = item.get_text(strip=True)
                break

        # Skills / tags
        tags = [s.get_text(strip=True) for s in card.select("div.job_skill") if s.get_text(strip=True)]

        # Description
        desc_el = card.select_one(".about_job .text")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        # Posted date for deadline inference
        posted_text = ""
        posted_el = card.select_one(".status-inactive span, .status_s span")
        if posted_el:
            posted_text = posted_el.get_text(strip=True)

        deadline = self._infer_deadline_from_posted(posted_text)

        # Company logo
        logo_el = card.select_one(".internship_logo img")
        image_url = ""
        if logo_el:
            src = logo_el.get("src", "")
            if src and "placeholder" not in src:
                image_url = src if src.startswith("http") else f"{self.BASE_URL}{src}"

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline if deadline else "",
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": image_url,
            "is_closed": False,
        }

    def _infer_deadline_from_posted(self, posted_text: str) -> str:
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
