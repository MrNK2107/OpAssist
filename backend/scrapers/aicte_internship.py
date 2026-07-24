import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, infer_deadline_from_posted

logger = logging.getLogger(__name__)


class AICTEInternshipScraper(GenericScraper):
    platform_name = "AICTEInternshipPortal"
    source_key = "aicte_internship"
    verticals = ["internship"]
    BASE_URL = "https://internship.aicte-india.org"
    LISTING_URLS = [
        f"{BASE_URL}/internship/list",
        BASE_URL,
    ]
    MAX_PAGES = 5

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for listing_url in self.LISTING_URLS:
            if all_items:
                break
            for page in range(1, self.MAX_PAGES + 1):
                if page == 1:
                    url = listing_url
                else:
                    url = f"{listing_url}?page={page}"
                logger.info(f"AICTE: fetching page {page}: {url}")

                try:
                    response = client.get(url, timeout=15)
                    if not response.is_success:
                        logger.warning(f"AICTE page {page}: HTTP {response.status_code}")
                        continue
                    items = self._parse_listing_page(response.text, page)
                    if not items:
                        logger.info(f"AICTE: no items on page {page}, trying next URL")
                        break
                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)
                    logger.info(f"AICTE: page {page} -> {len(items)} items")
                except Exception as exc:
                    logger.warning(f"AICTE page {page} error: {exc}")
                    continue

        logger.info(f"AICTE: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing_page(self, html_text: str, page: int) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = self._find_cards(soup)
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"AICTE: failed to parse card: {exc}")

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "tr",
            "div.card",
            "div[class*='row']",
            "div[class*='internship']",
            "div[class*='listing']",
            "div[class*='opportunity']",
            "div.internship-card",
            "div.internship-item",
            "div.job-card",
            "div.InternshipCard",
            "div[class*='Internship']",
            "div.post",
            "article",
        ]
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards
        return []

    def _parse_card(self, card) -> dict | None:
        title = self._extract_title(card)
        if not title:
            return None

        link = self._extract_link(card)
        if not link:
            return None

        organizer = self._extract_organizer(card)
        location = self._extract_location(card)
        stipend = self._extract_stipend(card)
        posted_text = self._extract_posted_date(card)
        tags = self._extract_tags(card)
        description = self._extract_description(card)

        if not description:
            description = f"Internship opportunity at {organizer}" if organizer else title

        deadline = infer_deadline_from_posted(posted_text)

        remote = "remote" in location.lower() if location else False

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": stipend,
            "date": deadline,
            "tags": ["Government", "AICTE"] + tags,
            "difficulty": "entry",
            "image_url": "",
            "employment_type": "internship",
            "remote": remote,
            "is_closed": False,
        }

    def _extract_title(self, card) -> str:
        selectors = [
            "a[href*='internship']",
            "h4 a",
            "h5 a",
            "h2 a",
            "h3 a",
            "h2",
            "h3",
            "h4",
            "h5",
            "td a",
            "a[class*='title']",
            "span[class*='title']",
            "div[class*='title'] a",
            "div[class*='heading'] a",
            "strong a",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 5:
                    return text
        return ""

    def _extract_link(self, card) -> str:
        selectors = [
            "a[href*='internship']",
            "a[href*='detail']",
            "a[href*='view']",
            "a[class*='title']",
            "h4 a",
            "h5 a",
            "h2 a",
            "h3 a",
            "a[href]",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                href = el.get("href", "")
                if href and href.strip():
                    return href if href.startswith("http") else f"{self.BASE_URL}{href}"
        return ""

    def _extract_organizer(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Organization")
        if labeled:
            return labeled
        selectors = [
            "td:nth-child(2)",
            "span[class*='org']",
            "div[class*='org']",
            "span.company",
            "div.company",
            "span[class*='company']",
            "div[class*='company']",
            "p[class*='company']",
            "[class*='organizer']",
            "[class*='employer']",
            "[class*='company-name']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 1:
                    return text
        return ""

    def _extract_location(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Location")
        if labeled:
            return labeled
        selectors = [
            "td:nth-child(3)",
            "span[class*='loc']",
            "div[class*='loc']",
            "[class*='location']",
            "[class*='Location']",
            "[class*='city']",
            "[class*='place']",
            "[class*='address']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_stipend(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Stipend")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        selectors = [
            "td:nth-child(4)",
            "span[class*='stipend']",
            "div[class*='stipend']",
            "[class*='stipend']",
            "[class*='salary']",
            "[class*='amount']",
            "[class*='pay']",
            "span[class*='price']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        return ""

    def _extract_tags(self, card) -> list[str]:
        labeled = self._extract_labeled_text(card, "Skills")
        if labeled:
            return [s.strip() for s in labeled.split(",") if s.strip()]
        selectors = [
            "td:nth-child(6)",
            "[class*='tag']",
            "[class*='skill']",
            "[class*='badge']",
            "[class*='category']",
            "[class*='tech']",
            "span[class*='label']",
        ]
        seen: set[str] = set()
        tags: list[str] = []
        for sel in selectors:
            for el in card.select(sel):
                text = el.get_text(strip=True)
                if text and text.lower() not in seen:
                    seen.add(text.lower())
                    tags.append(text)
        return tags

    def _extract_description(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Description")
        if labeled:
            return labeled[:500]
        selectors = [
            "td:nth-child(1)",
            "[class*='description']",
            "[class*='Description']",
            "[class*='about']",
            "[class*='desc']",
            "[class*='summary']",
            "[class*='details']",
            "p",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if len(text) > 20:
                    return text[:500]
        return ""

    def _extract_labeled_text(self, card, label: str) -> str:
        for strong in card.select("strong"):
            strong_text = strong.get_text(" ", strip=True).rstrip(":").strip().lower()
            if strong_text != label.lower():
                continue
            parent = strong.parent
            if not parent:
                continue
            text = parent.get_text(" ", strip=True)
            text = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", text, flags=re.IGNORECASE).strip()
            if text:
                return text
        return ""

    def _extract_posted_date(self, card) -> str:
        selectors = [
            "td:nth-child(6)",
            "span.date",
            "div.date",
            "[class*='posted']",
            "[class*='date']",
            "[class*='time']",
            "[class*='ago']",
            "[class*='created']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""
