import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, infer_deadline_from_posted

logger = logging.getLogger(__name__)


class SIHScraper(GenericScraper):
    """Smart India Hackathon scraper — India's flagship government hackathon.

    SIH is the single biggest hackathon in India (govt's flagship, software +
    hardware editions). Scrapes the official SIH website for current edition
    announcements, problem statements, and deadlines.
    """

    platform_name = "SIH"
    source_key = "sih"
    verticals = ["hackathon"]
    BASE_URL = "https://www.sih.gov.in"
    LISTING_URL = f"{BASE_URL}/sih2025"

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"SIH stage: fetching {self.LISTING_URL}")
        try:
            response = client.get(self.LISTING_URL, timeout=30)
            if not response.is_success:
                logger.warning(f"SIH: HTTP {response.status_code}")
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            items = self._parse_page(soup)
            logger.info(f"SIH stage: {len(items)} items")
            self._log_sample_links(items)
            return items
        except Exception as exc:
            logger.warning(f"SIH fetch failed: {exc}")
            return []

    def _parse_page(self, soup: BeautifulSoup) -> list[dict]:
        items: list[dict] = []
        page_text = soup.get_text()

        title_match = re.search(r"(Smart India Hackathon\s*\d{4})", page_text)
        title = title_match.group(1) if title_match else "Smart India Hackathon 2025"

        deadline = ""
        deadline_match = re.search(
            r"(?:last date|deadline|registration\s+closes?|apply\s+by)\s*:?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            page_text, re.IGNORECASE
        )
        if deadline_match:
            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    dt = datetime.strptime(deadline_match.group(1), fmt).replace(tzinfo=timezone.utc)
                    if dt > datetime.now(timezone.utc):
                        deadline = dt.strftime("%Y-%m-%d")
                        break
                except ValueError:
                    continue

        description = ""
        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc:
            description = meta_desc.get("content", "")[:1000]

        items.append({
            "title": title,
            "organizer": "Government of India",
            "start_date": "",
            "end_date": "",
            "date": deadline,
            "location": "India",
            "link": self.LISTING_URL,
            "description": description or f"India's flagship hackathon organized by the Ministry of Education's Innovation Cell. Software and hardware editions with problem statements from government departments.",
            "prize": "Prizes, recognition, and incubation opportunities",
            "tags": ["sih", "government", "india", "flagship", "hackathon", "ministry-of-education"],
            "difficulty": "intermediate",
            "type": "hackathon",
            "is_closed": False,
            "image_url": "",
        })

        return items
