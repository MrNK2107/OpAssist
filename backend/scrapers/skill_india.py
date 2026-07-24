import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class SkillIndiaScraper(GenericScraper):
    platform_name = "SkillIndiaPortal"
    source_key = "skill_india"
    verticals = ["job", "internship"]
    BASE_URL = "https://www.skillindia.gov.in"
    MAX_PAGES = 5
    TIMEOUT = 15

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        sections = [
            ("job", f"{self.BASE_URL}/jobs"),
            ("internship", f"{self.BASE_URL}/internships"),
        ]

        for item_type, base_url in sections:
            for page in range(1, self.MAX_PAGES + 1):
                url = f"{base_url}?page={page}" if page > 1 else base_url
                logger.info(f"SkillIndia: fetching {item_type} page {page}: {url}")

                try:
                    response = client.get(url, timeout=self.TIMEOUT)
                    if not response.is_success:
                        logger.warning(f"SkillIndia page {page} ({item_type}): HTTP {response.status_code}")
                        break
                    items = self._parse_listing_page(response.text, item_type)
                    if not items:
                        logger.info(f"SkillIndia: no items on {item_type} page {page}")
                        break
                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)
                    logger.info(f"SkillIndia: {item_type} page {page} -> {len(items)} items")
                except Exception as exc:
                    logger.warning(f"SkillIndia {item_type} page {page} error: {exc}")
                    break

        logger.info(f"SkillIndia: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing_page(self, html_text: str, default_type: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = self._find_cards(soup)
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card, default_type)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"SkillIndia: failed to parse card: {exc}")

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "tr",
            "div[class*='row']",
            "div.card",
            "div[class*='listing']",
            "li[class*='list']",
            "article",
            "div[class*='item']",
            "div[class*='card']",
            "div[class*='opportunity']",
            "div[class*='program']",
            "div[class*='training']",
            "div[class*='course']",
            "table tbody tr",
            "div[class*='result']",
            "div[class*='content']",
        ]
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards
        return []

    def _parse_card(self, card, default_type: str) -> dict | None:
        title = self._extract_title(card)
        if not title:
            return None

        link = self._extract_link(card)
        if not link:
            return None

        item_type = self._infer_type(card, link, default_type)
        organizer = self._extract_organizer(card)
        location = self._extract_location(card)
        stipend = self._extract_stipend(card)
        description = self._extract_description(card, title, organizer, location)
        posted_text = self._extract_posted_date(card)
        deadline = self._infer_deadline(posted_text)
        tags = self._extract_tags(card)
        image_url = self._extract_image_url(card)

        employment_type = "internship" if item_type == "internship" else "full-time"
        remote = "remote" in location.lower() if location else False

        return {
            "title": title,
            "type": item_type,
            "link": link,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": stipend,
            "date": deadline,
            "tags": tags,
            "difficulty": "entry",
            "image_url": image_url,
            "employment_type": employment_type,
            "remote": remote,
            "is_closed": False,
        }

    def _extract_title(self, card) -> str:
        selectors = [
            "a[href*='job']",
            "a[href*='internship']",
            "h2 a",
            "h3 a",
            "h4 a",
            "strong a",
            "td a",
            "h2",
            "h3",
            "h4",
            "strong",
            "a[class*='title']",
            "span[class*='title']",
            "div[class*='title'] a",
            "div[class*='heading'] a",
            "a[href]",
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
            "a[href*='job']",
            "a[href*='internship']",
            "a[href*='training']",
            "a[href*='program']",
            "a[class*='title']",
            "h2 a",
            "h3 a",
            "h4 a",
            "strong a",
            "td a",
            "a[href]",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                href = el.get("href", "")
                if href and href != "#":
                    return href if href.startswith("http") else f"{self.BASE_URL}{href}"
        return ""

    def _infer_type(self, card, link: str, default_type: str) -> str:
        link_lower = link.lower()
        if "internship" in link_lower:
            return "internship"
        if "job" in link_lower:
            return "job"

        card_text = card.get_text(" ", strip=True).lower()
        if "internship" in card_text:
            return "internship"
        if "job" in card_text or "vacancy" in card_text or "recruitment" in card_text:
            return "job"

        return default_type

    def _extract_organizer(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Organization")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "Company")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "Organizer")
        if labeled:
            return labeled
        selectors = [
            "span[class*='org']",
            "td:nth-child(2)",
            ".company",
            "span[class*='comp']",
            "span[class*='organizer']",
            "div[class*='org']",
            "div[class*='company']",
            "p[class*='org']",
            "p[class*='company']",
            "[class*='organization']",
            "[class*='employer']",
            "[class*='agency']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 2:
                    return text
        return ""

    def _extract_location(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Location")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "Place")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "City")
        if labeled:
            return labeled
        selectors = [
            "span[class*='loc']",
            "td:nth-child(3)",
            ".location",
            "span[class*='location']",
            "div[class*='location']",
            "[class*='city']",
            "[class*='place']",
            "[class*='address']",
            "td:nth-child(4)",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 2:
                    return text
        return ""

    def _extract_stipend(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Stipend")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        labeled = self._extract_labeled_text(card, "Salary")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        labeled = self._extract_labeled_text(card, "Amount")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        labeled = self._extract_labeled_text(card, "Honorarium")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        selectors = [
            "span[class*='stipend']",
            "span[class*='salary']",
            "span[class*='amount']",
            "span[class*='pay']",
            "span[class*='price']",
            "td:nth-child(4)",
            "td:nth-child(5)",
            "[class*='stipend']",
            "[class*='salary']",
            "[class*='amount']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    text = text.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
                    return text
        return ""

    def _extract_description(self, card, title: str = "", organizer: str = "", location: str = "") -> str:
        selectors = [
            "[class*='description']",
            "[class*='Description']",
            "[class*='about']",
            "[class*='desc']",
            "[class*='summary']",
            "[class*='details']",
            "td:nth-child(5)",
            "p",
            "td p",
            "div[class*='text']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if len(text) > 20:
                    return text[:500]
        parts = [title]
        if organizer:
            parts.append(f"at {organizer}")
        if location:
            parts.append(f"in {location}")
        return " - ".join(parts) if len(parts) > 1 else title

    def _extract_tags(self, card) -> list[str]:
        tags = ["Skill India", "Government"]
        selectors = [
            "[class*='tag']",
            "[class*='skill']",
            "[class*='category']",
            "[class*='badge']",
            "[class*='sector']",
            "[class*='field']",
            "[class*='stream']",
        ]
        seen: set[str] = set(t.lower() for t in tags)
        for sel in selectors:
            for el in card.select(sel):
                text = el.get_text(strip=True)
                if text and text.lower() not in seen:
                    seen.add(text.lower())
                    tags.append(text)
        return tags

    def _extract_posted_date(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Posted")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "Date")
        if labeled:
            return labeled
        labeled = self._extract_labeled_text(card, "Last Date")
        if labeled:
            return labeled
        selectors = [
            "[class*='posted']",
            "[class*='date']",
            "[class*='Date']",
            "[class*='time']",
            "[class*='ago']",
            "[class*='deadline']",
            "td:nth-child(6)",
            "span[class*='days']",
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
            "img[class*='gov']",
            "img[class*='icon']",
            "div[class*='logo'] img",
            "img[src*='logo']",
            "img",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                src = el.get("src", "")
                if src and "placeholder" not in src.lower() and "data:image" not in src:
                    return src if src.startswith("http") else f"{self.BASE_URL}{src}"
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

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month|hr|hour|min)", posted_text, re.IGNORECASE)
        if not match:
            if any(kw in posted_text.lower() for kw in ("today", "just now", "just posted", "recently", "open")):
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            try:
                dt = datetime.strptime(posted_text[:10], "%Y-%m-%d")
                deadline_dt = dt + timedelta(days=30)
                return deadline_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
            return ""
        count = int(match.group(1))
        unit = match.group(2).lower()
        if "month" in unit:
            days_ago = count * 30
        elif "week" in unit:
            days_ago = count * 7
        elif "hour" in unit or "min" in unit:
            days_ago = 0
        else:
            days_ago = count
        days_remaining = max(0, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
