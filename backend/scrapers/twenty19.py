import logging
import re
from datetime import datetime, timezone, timedelta

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class Twenty19Scraper(GenericScraper):
    platform_name = "Twenty19"
    source_key = "twenty19"
    verticals = ["internship"]
    requires_playwright = True
    BASE_URL = "https://www.twenty19.com"
    LISTING_URL = f"{BASE_URL}/internships"
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        items = self._fetch_listings(client)
        if items:
            logger.info(f"Twenty19: {len(items)} items scraped via httpx")
            return items
        logger.info("Twenty19: httpx returned no items, trying Playwright fallback")
        return self._with_playwright(self._playwright_scrape)

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Twenty19 (Playwright): starting scrape")
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page_num in range(1, self.MAX_PAGES + 1):
            url = f"{self.LISTING_URL}?page={page_num}" if page_num > 1 else self.LISTING_URL
            logger.info(f"Twenty19 (Playwright): fetching page {page_num}: {url}")

            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)

                try:
                    page.wait_for_selector(
                        "div.internship-card, div.card, div.listing-item, "
                        "div[class*='internship'], article",
                        timeout=15000,
                    )
                except Exception:
                    logger.warning(f"Twenty19 (Playwright): no cards on page {page_num}")
                    break

                html = page.content()
                items = self._parse_page(html)
                for item in items:
                    link = item.get("link", "")
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        all_items.append(item)
                if not items:
                    break
            except Exception as e:
                logger.warning(f"Twenty19 (Playwright): error on page {page_num}: {e}")
                break

        logger.info(f"Twenty19 (Playwright): {len(all_items)} total items")
        return all_items

    def _fetch_listings(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.LISTING_URL}?page={page}" if page > 1 else self.LISTING_URL
            logger.info(f"Twenty19: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"Twenty19 page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_page(response.text)
                for item in items:
                    link = item.get("link", "")
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        all_items.append(item)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"Twenty19 page {page} error: {exc}")
                break

        return all_items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "div.internship-card",
            "div.card",
            "div.listing-item",
            "div.internship-item",
            "div.job-card",
            "div[class*='internship']",
            "div[class*='listing']",
            "div[class*='card']",
            "article",
            "li[class*='internship']",
            "li[class*='job']",
            "a[href*='/internship/']",
        ]
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards
        return []

    def _parse_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = self._find_cards(soup)
        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Twenty19: failed to parse card: {exc}")
        return items

    def _parse_card(self, card) -> dict | None:
        title = self._extract_title(card)
        if not title:
            return None

        link = self._extract_link(card)
        if not link:
            return None

        company = self._extract_company(card)
        location = self._extract_location(card)
        stipend = self._extract_stipend(card)
        duration = self._extract_duration(card)
        tags = self._extract_tags(card)
        description = self._extract_description(card)
        posted_text = self._extract_posted_text(card)
        deadline = self._infer_deadline_from_posted(posted_text)
        image_url = self._extract_image(card)

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": stipend,
            "date": deadline,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": image_url,
            "is_closed": False,
            "duration": duration,
            "start_date": posted_text,
        }

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

    def _extract_title(self, card) -> str:
        selectors = [
            "h2 a", "h3 a", "h2", "h3",
            "a[class*='title']", "span[class*='title']",
            "div[class*='title'] a",
            "div[class*='heading'] a",
            "a[href*='/internship/']",
            ".internship-title a",
            ".card-title a",
            ".job-title a",
            ".title a",
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
            "a[href*='/internship-detail/']",
            "a.internship-link",
            "a.card-link",
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

    def _extract_company(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Company")
        if labeled:
            return labeled
        selectors = [
            ".company-name",
            ".company",
            ".organizer",
            ".provider",
            "[class*='company']",
            "[class*='organizer']",
            "[class*='Company']",
            "p:first-of-type",
            "span:first-of-type",
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
            "[class*='loc']",
            "[class*='place']",
            "[class*='city']",
            ".location",
            ".locations",
            ".place",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        icons = card.select("span[class*='icon'], i[class*='icon']")
        for icon in icons:
            parent = icon.parent
            if parent:
                text = parent.get_text(strip=True)
                if text:
                    icon_text = icon.get_text(strip=True)
                    if icon_text:
                        text = text.replace(icon_text, "").strip()
                    return text
        return ""

    def _extract_stipend(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Stipend")
        if labeled:
            return labeled
        selectors = [
            "[class*='stipend']",
            "[class*='salary']",
            "[class*='prize']",
            "[class*='compensation']",
            "[class*='Stipend']",
            "[class*='amount']",
            "[class*='pay']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        for el in card.find_all(["span", "p", "div"]):
            text = el.get_text(strip=True)
            if re.search(r"[₹Rs.\s]*[\d,]+", text) and any(
                kw in text.lower() for kw in ["stipend", "salary", "pay", "month"]
            ):
                return text
        return ""

    def _extract_duration(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Duration")
        if labeled:
            return labeled
        selectors = [
            "[class*='duration']",
            "[class*='Duration']",
            "[class*='tenure']",
            "[class*='period']",
            "[class*='month']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        for el in card.find_all(["span", "p", "div"]):
            text = el.get_text(strip=True).lower()
            if re.search(r"\d+\s*(month|week|year)", text) and len(text) < 30:
                return el.get_text(strip=True)
        return ""

    def _extract_tags(self, card) -> list[str]:
        labeled_category = self._extract_labeled_text(card, "Category")
        if labeled_category:
            return [labeled_category]
        selectors = [
            "[class*='skill']",
            "[class*='tag']",
            "[class*='badge']",
            "[class*='category']",
            ".skills span",
            ".tags span",
            ".skill-tag",
            ".tag",
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
        selectors = [
            "[class*='description']",
            "[class*='Description']",
            "[class*='summary']",
            "[class*='about']",
            "[class*='desc']",
            "[class*='details']",
            ".description",
            ".desc",
            ".about",
            ".summary",
            "p",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if len(text) > 20:
                    return re.sub(r"\s+", " ", text)[:500]
        return ""

    def _extract_posted_text(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Posted")
        if labeled:
            return labeled
        selectors = [
            "[class*='posted']",
            "[class*='Posted']",
            "[class*='date']",
            "[class*='time']",
            "[class*='ago']",
            "[class*='created']",
            ".posted",
            ".posted-date",
            ".date",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        for el in card.find_all(["span", "p", "small"]):
            text = el.get_text(strip=True).lower()
            if any(kw in text for kw in ["day", "week", "month", "hour", "minute", "today", "ago"]):
                return el.get_text(strip=True)
        return ""

    def _extract_image(self, card) -> str:
        selectors = [
            "img[class*='logo']",
            "img[class*='company']",
            "img[class*='avatar']",
            "img[class*='thumb']",
            "div[class*='logo'] img",
            "div[class*='icon'] img",
            "img[src*='logo']",
            "img",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                src = el.get("src", "") or el.get("data-src", "")
                if src and "placeholder" not in src.lower() and "blank" not in src.lower():
                    return src if src.startswith("http") else f"{self.BASE_URL}{src}"
        return ""

    def _infer_deadline_from_posted(self, posted_text: str) -> str:
        if not posted_text:
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE)
        if not match:
            if any(kw in posted_text.lower() for kw in ["today", "just now", "hour", "minute"]):
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

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
