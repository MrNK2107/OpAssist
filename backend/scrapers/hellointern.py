import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class HelloInternScraper(GenericScraper):
    platform_name = "HelloIntern"
    source_key = "hellointern"
    verticals = ["internship"]
    BASE_URL = "https://hellointern.in"
    LISTING_URL = f"{BASE_URL}/internships"
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.LISTING_URL}?page={page}" if page > 1 else self.LISTING_URL
            logger.info(f"HelloIntern: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"HelloIntern page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text, page)
                if not items:
                    logger.info(f"HelloIntern: no items on page {page}, stopping pagination")
                    break
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                logger.info(f"HelloIntern: page {page} -> {len(items)} items")
            except Exception as exc:
                logger.warning(f"HelloIntern page {page} error: {exc}")
                break

        logger.info(f"HelloIntern: {len(all_items)} total items")
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
                logger.debug(f"HelloIntern: failed to parse card: {exc}")

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        listing_articles = soup.select("section[aria-label='Internship Listings'] article")
        if listing_articles:
            return listing_articles

        selectors = [
            "div.internship-card",
            "div.card",
            "div.listing-card",
            "div.internship-item",
            "div[class*='internship']",
            "div[class*='listing']",
            "div[class*='card']",
            "article",
            "a[href*='/internship/detail/']",
            "a[href*='/internship/']",
            "div.post",
            "div.job-card",
            "div.opportunity-card",
            "div.InternshipCard",
            "div[class*='Internship']",
            "div[class*='JobCard']",
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
        duration = self._extract_duration(card)
        tags = self._extract_tags(card)
        description = self._extract_description(card)
        posted_text = self._extract_posted_date(card)
        image_url = self._extract_image_url(card)
        deadline = self._infer_deadline(posted_text)
        employment_type = self._extract_labeled_text(card, "Type").lower().replace("_", "-")
        remote = "remote" in location.lower()

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": stipend,
            "date": deadline if deadline else "",
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": image_url,
            "duration": duration,
            "employment_type": employment_type or None,
            "remote": remote,
            "is_closed": False,
        }

    def _extract_title(self, card) -> str:
        selectors = [
            "h2 a", "h3 a", "h2", "h3",
            "a[class*='title']", "span[class*='title']",
            "div[class*='title'] a",
            "div[class*='heading'] a",
            "a[href*='/internship/']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    href = el.get("href", "") if el.name == "a" else ""
                    if href and "/internship/" in href:
                        return text
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_link(self, card) -> str:
        selectors = [
            "a[href*='/internship/']",
            "a[href*='/job/']",
            "a[class*='title']",
            "h2 a", "h3 a",
            "div[class*='title'] a",
            "a[href]",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                href = el.get("href", "")
                if href:
                    return href if href.startswith("http") else f"{self.BASE_URL}{href}"
        return ""

    def _extract_organizer(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Company")
        if labeled:
            return labeled
        selectors = [
            "p[class*='company']",
            "span[class*='company']",
            "div[class*='company']",
            "p[class*='organizer']",
            "span[class*='org']",
            "div[class*='org']",
            "p[class*='employer']",
            "span[class*='employer']",
            "[class*='company-name']",
            "[class*='CompanyName']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_location(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Location")
        if labeled:
            return labeled
        selectors = [
            "[class*='location']",
            "[class*='Location']",
            "[class*='city']",
            "[class*='place']",
            "span[class*='loc']",
            "div[class*='loc']",
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
            "[class*='stipend']",
            "[class*='salary']",
            "[class*='prize']",
            "[class*='Stipend']",
            "[class*='amount']",
            "[class*='pay']",
            "span[class*='price']",
            "span[class*='money']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    text = text.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
                    return text
        return ""

    def _extract_duration(self, card) -> str:
        selectors = [
            "[class*='duration']",
            "[class*='Duration']",
            "[class*='period']",
            "[class*='tenure']",
            "[class*='month']",
            "span[class*='time']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_tags(self, card) -> list[str]:
        labeled_category = self._extract_labeled_text(card, "Category")
        if labeled_category:
            return [labeled_category]
        selectors = [
            "[class*='tag']",
            "[class*='skill']",
            "[class*='badge']",
            "[class*='category']",
            "[class*='tech']",
            "span[class*='label']",
            "ul li a[href*='keyword']",
            "a[href*='keyword']",
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
        category = self._extract_labeled_text(card, "Category")
        employment_type = self._extract_labeled_text(card, "Type")
        if category or employment_type:
            parts = []
            if category:
                parts.append(f"Category: {category}")
            if employment_type:
                parts.append(f"Type: {employment_type}")
            return " | ".join(parts)
        selectors = [
            "[class*='description']",
            "[class*='Description']",
            "[class*='about']",
            "[class*='desc']",
            "[class*='summary']",
            "p",
            "div[class*='text']",
            "[class*='details']",
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
            "[class*='posted']",
            "[class*='date']",
            "[class*='time']",
            "[class*='ago']",
            "[class*='created']",
            "span[class*='days']",
            "[class*='status']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_image_url(self, card) -> str:
        selectors = [
            "img[class*='logo']",
            "img[class*='company']",
            "img[class*='avatar']",
            "div[class*='logo'] img",
            "div[class*='icon'] img",
            "img[src*='logo']",
            "img",
        ]
        seen_srcs: set[str] = set()
        for sel in selectors:
            for el in card.select(sel):
                src = el.get("src", "")
                if src and "placeholder" not in src.lower() and "data:image" not in src:
                    if src not in seen_srcs:
                        seen_srcs.add(src)
                        return src if src.startswith("http") else f"{self.BASE_URL}{src}"
        return ""

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE)
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
