import logging
import re
from datetime import datetime, timezone
from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class TechGigScraper(GenericScraper):
    platform_name = "TechGig"
    source_key = "techgig"
    verticals = ["hackathon"]
    BASE_URL = "https://techgig.com"
    LISTING_URL = f"{BASE_URL}/hackathons"
    MAX_PAGES = 1

    requires_playwright = False

    def scrape(self, client: httpx.Client) -> list[dict]:
        logger.info(f"TechGig stage: fetching {self.LISTING_URL}")
        response = client.get(self.LISTING_URL, follow_redirects=True)
        if not response.is_success:
            logger.warning(f"TechGig request failed with status {response.status_code}")
            logger.info("TechGig: httpx failed, falling back to Playwright")
            return self._with_playwright(self.scrape_playwright)

        soup = BeautifulSoup(response.text, "html.parser")
        items = self._parse_listing(soup)

        if items:
            logger.info(f"TechGig stage: page 1 items={len(items)}")
            for page in range(2, self.MAX_PAGES + 1):
                page_items = self._fetch_page(client, page)
                if not page_items:
                    break
                items.extend(page_items)
                logger.info(f"TechGig stage: page {page} items={len(page_items)}")

        if not items:
            logger.info("TechGig: httpx returned 0 items, falling back to Playwright")
            return self._with_playwright(self.scrape_playwright)

        logger.info(f"TechGig stage: total items={len(items)}")
        self._log_sample_links(items)
        return items

    def scrape_playwright(self, page) -> list[dict]:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        logger.info(f"TechGig stage (Playwright): navigating to {self.LISTING_URL}")
        page.goto(self.LISTING_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        items = self._parse_listing(BeautifulSoup(page.content(), "html.parser"))

        if items:
            logger.info(f"TechGig stage (Playwright): page 1 items={len(items)}")
            for p in range(2, self.MAX_PAGES + 1):
                next_url = self._find_next_page_playwright(page)
                if not next_url:
                    logger.info("TechGig (Playwright): no more pages")
                    break
                page.goto(next_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                page_items = self._parse_listing(BeautifulSoup(page.content(), "html.parser"))
                if not page_items:
                    break
                items.extend(page_items)
                logger.info(f"TechGig stage (Playwright): page {p} items={len(page_items)}")

        logger.info(f"TechGig stage (Playwright): total items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_page(self, client: httpx.Client, page_num: int) -> list[dict]:
        pagination_url = self._build_page_url(page_num)
        logger.info(f"TechGig: fetching page {page_num} via {pagination_url}")
        try:
            response = client.get(pagination_url)
            if not response.is_success:
                return []
            soup = BeautifulSoup(response.text, "html.parser")
            items = self._parse_listing(soup)
            if not items:
                logger.info(f"TechGig: page {page_num} returned no items, stopping pagination")
            return items
        except Exception as exc:
            logger.warning(f"TechGig page {page_num} error: {exc}")
            return []

    def _build_page_url(self, page_num: int) -> str:
        if page_num <= 1:
            return self.LISTING_URL
        return f"{self.LISTING_URL}?page={page_num}"

    def _find_next_page_playwright(self, page) -> Optional[str]:
        try:
            next_el = page.query_selector("a[rel='next'], .pagination .next a, a:has-text('Next')")
            if next_el:
                href = next_el.get_attribute("href")
                if href:
                    return href if href.startswith("http") else f"{self.BASE_URL}{href}"
        except Exception as exc:
            logger.warning(f"TechGig find_next_page error: {exc}")
        return None

    def _parse_listing(self, soup: BeautifulSoup) -> list[dict]:
        items: list[dict] = []
        now = datetime.now(timezone.utc)
        cards = self._find_cards(soup)

        if not cards:
            logger.info("TechGig: no hackathon cards found on this page")
            return []

        for card in cards:
            try:
                item = self._parse_card(card, now)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.warning(f"TechGig: error parsing card: {exc}")
                continue

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        cards = soup.select("a.challenge-card")
        if cards:
            logger.info(f"TechGig: found {len(cards)} cards via 'a.challenge-card'")
            return cards

        cards = soup.find_all("div", class_=re.compile(r"(?i)hackathon|contest|challenge-card|card-item"))
        if cards:
            logger.info(f"TechGig: found {len(cards)} cards via regex")
            return cards

        return []
    def _parse_card(self, card, now: datetime) -> Optional[dict]:
        href = card.get("href", "")
        if not href or href.startswith("#") or href.startswith("javascript"):
            return None
        if not href.startswith("http"):
            href = f"{self.BASE_URL}{href}"

        title_el = card.find("h4")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        organizer_el = card.select_one(".tm-past-contests-media-brand")
        organizer = organizer_el.get_text(strip=True) if organizer_el else ""

        desc_el = card.select_one(".content p")
        description = desc_el.get_text(strip=True)[:1000] if desc_el else ""

        tags_el = card.select_one(".quiz-card__skills")
        tags = []
        if tags_el:
            tags = [
                tag.get_text(" ", strip=True)
                for tag in tags_el.select(".quiz__skill, span")
                if tag.get_text(" ", strip=True)
            ][:10]

        participants_el = card.select_one(".current_users_count")
        participants_text = participants_el.get_text(strip=True) if participants_el else ""

        img_el = card.find("img")
        image_url = ""
        if img_el:
            src = img_el.get("src") or img_el.get("data-src") or ""
            if src and not src.startswith("data:"):
                image_url = src if src.startswith("http") else f"{self.BASE_URL}{src}"

        difficulty = self._infer_difficulty(tags)

        return {
            "title": title,
            "organizer": organizer,
            "start_date": None,
            "end_date": None,
            "date": "",
            "location": "Online",
            "link": href,
            "source_platform": "TechGig",
            "description": description,
            "prize": "",
            "tags": tags,
            "difficulty": difficulty,
            "type": "hackathon",
            "is_closed": False,
            "image_url": image_url,
        }

    @staticmethod
    def _parse_deadline(raw: str) -> Optional[datetime]:
        if not raw:
            return None
        raw = raw.strip()
        now = datetime.now(timezone.utc)

        formats = [
            "%d %b %Y",
            "%d %B %Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%d %b %y",
            "%d %B %y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        m = re.search(r"(\d{1,2})\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{4})", raw, re.I)
        if m:
            try:
                return datetime.strptime(m.group(0), "%d %b %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            except ValueError:
                pass

        if "day" in raw.lower():
            m = re.search(r"(\d+)", raw)
            if m:
                days = int(m.group(1))
                return now.replace(hour=23, minute=59, second=59) + __import__("datetime").timedelta(days=days)

        return None
