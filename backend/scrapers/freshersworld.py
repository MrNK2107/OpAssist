import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class FreshersworldScraper(GenericScraper):
    platform_name = "Freshersworld"
    source_key = "freshersworld"
    verticals = ["job", "internship"]
    BASE_URL = "https://www.freshersworld.com"
    MAX_PAGES = 5

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for vertical in self.verticals:
            section = "internships" if vertical == "internship" else "jobs"
            for page in range(1, self.MAX_PAGES + 1):
                url = f"{self.BASE_URL}/{section}?page={page}" if page > 1 else f"{self.BASE_URL}/{section}"
                logger.info(f"Freshersworld: fetching {section} page {page}: {url}")

                try:
                    response = client.get(url, timeout=30)
                    if response.status_code == 403:
                        raise ScrapeBlockedError(source=self.source_key, status_code=403)
                    if not response.is_success:
                        logger.warning(f"Freshersworld {section} page {page}: HTTP {response.status_code}")
                        break

                    items = self._parse_listing_page(response.text, vertical)
                    if not items:
                        logger.info(f"Freshersworld: no items on {section} page {page}, stopping pagination")
                        break

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(f"Freshersworld: {section} page {page} -> {len(items)} items")
                except ScrapeBlockedError:
                    raise
                except Exception as exc:
                    logger.warning(f"Freshersworld {section} page {page} error: {exc}")
                    break

        logger.info(f"Freshersworld: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing_page(self, html_text: str, vertical: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = self._find_cards(soup)
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card, vertical)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Freshersworld: failed to parse card: {exc}")

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "div.job-card",
            "div[class*='job-card']",
            "div[class*='listing']",
            "div.card",
            "li[class*='job']",
            "div[class*='opportunity']",
            "div.listing-card",
            "div.internship-card",
            "div[class*='internship-card']",
            "div[class*='JobCard']",
            "div[class*='InternshipCard']",
            "div[class*='job-listing']",
            "div[class*='internship-listing']",
            "article",
        ]
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                return cards
        return []

    def _parse_card(self, card, vertical: str) -> dict | None:
        title = self._extract_title(card)
        if not title:
            return None

        link = self._extract_link(card)
        if not link:
            return None

        organizer = self._extract_organizer(card)
        location = self._extract_location(card)
        salary = self._extract_salary(card)
        tags = self._extract_tags(card)
        posted_text = self._extract_posted_date(card)
        image_url = self._extract_image_url(card)
        description = self._extract_description(card)
        experience = self._extract_experience(card)

        if not description:
            description = self._build_description(title, organizer, location, experience, tags)

        deadline = self._infer_deadline(posted_text)
        remote = "remote" in location.lower() or "work from home" in (title + " " + " ".join(tags)).lower()

        return {
            "title": title,
            "type": vertical,
            "link": link,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline if deadline else "",
            "tags": tags,
            "difficulty": self._resolve_experience_level(None, None, title, tags),
            "image_url": image_url,
            "employment_type": "full-time" if vertical == "job" else "internship",
            "remote": remote,
            "is_closed": False,
            "salary_currency": "INR" if salary else "",
        }

    def _extract_title(self, card) -> str:
        for sel in ['h2 a', 'h3 a', 'a[class*="title"]', '.job-title-href a']:
            el = card.select_one(sel)
            if el:
                return el.get_text(strip=True)
        for sel in ['a[href*="/job/"]', 'a[href*="/internship/"]']:
            el = card.select_one(sel)
            if el:
                return el.get_text(strip=True)
        for sel in ['a[class*="job"]', 'a[class*="internship"]', 'a[class*="title"]', 'h2', 'h3']:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_link(self, card) -> str:
        for sel in ['a[href*="/job/"]', 'a[href*="/internship/"]', 'a[class*="title"]', 'h2 a', 'h3 a', 'a[href]']:
            el = card.select_one(sel)
            if el:
                href = el.get("href", "")
                if href:
                    return href if href.startswith("http") else f"{self.BASE_URL}{href}"
        return ""

    def _extract_organizer(self, card) -> str:
        selectors = [
            "[class*='company-name']",
            "[class*='comp-name']",
            "[class*='company']",
            "[class*='CompanyName']",
            "[class*='organizer']",
            "[class*='org']",
            "[class*='employer']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_location(self, card) -> str:
        selectors = [
            "[class*='location']",
            "[class*='loc-detail']",
            "[class*='loc']",
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

    def _extract_salary(self, card) -> str:
        selectors = [
            "[class*='salary']",
            "[class*='package']",
            "[class*='stipend']",
            "[class*='pay']",
            "[class*='prize']",
            "[class*='amount']",
            "[class*='money']",
            "[class*='Price']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        return ""

    def _extract_tags(self, card) -> list[str]:
        selectors = [
            "[class*='skill']",
            "[class*='tag']",
            "[class*='badge']",
            "[class*='category']",
            "[class*='tech']",
            "[class*='keyskill']",
            "[class*='KeySkill']",
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

    def _extract_posted_date(self, card) -> str:
        selectors = [
            "[class*='posted']",
            "[class*='date']",
            "[class*='time']",
            "[class*='days']",
            "[class*='ago']",
            "[class*='created']",
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

    def _extract_description(self, card) -> str:
        selectors = [
            "[class*='description']",
            "[class*='desc']",
            "[class*='about']",
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

    def _extract_experience(self, card) -> str:
        selectors = [
            "[class*='experience']",
            "[class*='exp']",
            "[class*='Exp']",
            "[class*='year']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*(yr|year|yrs)?", text, re.IGNORECASE)
                    if match:
                        return text
                    match = re.search(r"(\d+)\s*[-–]?\s*(\d+)\s*(yr|year|yrs)", text, re.IGNORECASE)
                    if match:
                        return text
                    match = re.search(r"(\d+)\s*(yr|year|yrs)", text, re.IGNORECASE)
                    if match:
                        return text
        return ""

    def _build_description(self, title: str, company: str, location: str, experience: str, tags: list[str]) -> str:
        parts = [title]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"in {location}")
        if experience:
            parts.append(f"requiring {experience} experience")
        if tags:
            parts.append("skills: " + ", ".join(tags[:5]))
        return " ".join(parts) + "."

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month|hr|hour|min)", posted_text, re.IGNORECASE)
        if not match:
            if any(kw in posted_text.lower() for kw in ("today", "just now", "just posted", "moments ago", "recently")):
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
