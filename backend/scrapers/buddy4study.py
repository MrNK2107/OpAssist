import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class Buddy4StudyScraper(GenericScraper):
    """Buddy4Study scraper — scholarships from buddy4study.com.

    India's largest scholarship aggregator. Scrapes HTML listing pages.
    """

    platform_name = "Buddy4Study"
    BASE_URL = "https://www.buddy4study.com"
    LISTING_URL = f"{BASE_URL}/scholarships"
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.LISTING_URL}?page={page}" if page > 1 else self.LISTING_URL
            logger.info(f"Buddy4Study: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"Buddy4Study page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"Buddy4Study page {page} error: {exc}")
                break

        logger.info(f"Buddy4Study: {len(all_items)} total items")
        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        """Extract scholarship data from a listing page."""
        soup = BeautifulSoup(html_text, "html.parser")
        # Buddy4Study uses scholarship card containers
        cards = soup.select(
            "div.scholarship-card, div.scholarship-listing-card, "
            "div.card-body, article.scholarship-item, "
            "div[class*='scholarship'][class*='card']"
        )
        if not cards:
            # Fallback: look for links that match scholarship pattern
            cards = soup.select("a[href*='/scholarship/']")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Buddy4Study: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        """Parse a single scholarship card."""
        # If the card is an anchor tag itself
        if card.name == "a":
            title = card.get_text(strip=True)[:200]
            link = card.get("href", "")
            if not title or not link:
                return None
            link = link if link.startswith("http") else f"{self.BASE_URL}{link}"
            return self._build_item(title, link, "", "", "", "")

        # Title — try multiple selectors
        title_el = card.select_one(
            "h3 a, h4 a, h2 a, a.scholarship-title, "
            "div[class*='title'] a, a[href*='/scholarship/']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            # Try just h3/h4/h2 text
            heading = card.select_one("h3, h4, h2")
            title = heading.get_text(strip=True) if heading else ""
        if not title:
            return None

        # Link
        href = ""
        if title_el and title_el.name == "a":
            href = title_el.get("href", "")
        if not href:
            link_el = card.select_one("a[href*='/scholarship/']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Organizer / provider
        organizer_el = card.select_one(
            "span[class*='provider'], span[class*='organization'], "
            "div[class*='provider'], p[class*='provider']"
        )
        organizer = organizer_el.get_text(strip=True) if organizer_el else ""

        # Deadline
        deadline_el = card.select_one(
            "span[class*='deadline'], span[class*='date'], "
            "div[class*='deadline'], div[class*='date']"
        )
        deadline = ""
        if deadline_el:
            deadline = self._parse_deadline_text(deadline_el.get_text(strip=True))

        # Amount / prize
        amount_el = card.select_one(
            "span[class*='amount'], span[class*='prize'], "
            "div[class*='amount'], div[class*='reward']"
        )
        amount = amount_el.get_text(strip=True) if amount_el else ""

        # Eligibility / tags
        tags = []
        tag_els = card.select("span.badge, span.tag, div[class*='tag'], span[class*='eligibility']")
        for tag_el in tag_els:
            text = tag_el.get_text(strip=True)
            if text and len(text) < 50:
                tags.append(text)

        return self._build_item(title, link, organizer, deadline, amount, tags)

    def _build_item(self, title: str, link: str, organizer: str, deadline: str, amount: str, tags) -> dict:
        return {
            "title": title,
            "type": "scholarship",
            "link": link,
            "organizer": organizer,
            "description": "",
            "location": "India",
            "prize": amount,
            "date": deadline,
            "tags": tags if isinstance(tags, list) else [],
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }

    def _parse_deadline_text(self, text: str) -> str:
        """Parse deadline text like '31 May 2026', 'May 31, 2026', etc."""
        if not text:
            return ""
        # Remove common prefixes
        text = re.sub(r"(?i)deadline\s*:?\s*", "", text).strip()
        text = re.sub(r"(?i)last\s+date\s*:?\s*", "", text).strip()

        for fmt in ["%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
                     "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                dt = datetime.strptime(text.strip(), fmt).replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return ""
