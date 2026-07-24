import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class WorkIndiaScraper(GenericScraper):
    platform_name = "WorkIndia"
    source_key = "workindia"
    verticals = ["job"]
    BASE_URL = "https://www.workindia.in"
    MAX_PAGES = 3
    CITIES = ["bangalore", "mumbai", "delhi", "hyderabad", "pune", "chennai", "kolkata", "ahmedabad"]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        # First, try the general feed
        try:
            items = self._scrape_city(client, "jobs", seen_urls)
            logger.info(f"WorkIndia: general feed -> {len(items)} items")
            all_items.extend(items)
        except ScrapeBlockedError:
            logger.warning("WorkIndia: general feed blocked")
        except Exception as exc:
            logger.warning(f"WorkIndia: general feed error: {exc}")

        # Then scrape each city
        for city in self.CITIES:
            if len(all_items) >= 100:
                break
            try:
                items = self._scrape_city(client, f"jobs-in-{city}", seen_urls)
                if items:
                    logger.info(f"WorkIndia: {city} -> {len(items)} items")
                    all_items.extend(items)
            except ScrapeBlockedError:
                logger.warning(f"WorkIndia: {city} blocked, skipping")
                continue
            except Exception as exc:
                logger.warning(f"WorkIndia: {city} error: {exc}")
                continue

        logger.info(f"WorkIndia: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _scrape_city(self, client: httpx.Client, path: str, seen_urls: set[str]) -> list[dict]:
        items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.BASE_URL}/{path}/" if page == 1 else f"{self.BASE_URL}/{path}/?page={page}"
            logger.info(f"WorkIndia: fetching {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(source=self.source_key, status_code=403)
                if not response.is_success:
                    logger.warning(f"WorkIndia: HTTP {response.status_code} for {url}")
                    break

                parsed = self._parse_listing_page(response.text)
                if not parsed:
                    logger.info(f"WorkIndia: no items on page {page} for {path}")
                    break

                for item in parsed:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        items.append(item)

            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"WorkIndia: page {page} error: {exc}")
                break

        return items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = self._find_cards(soup)
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"WorkIndia: failed to parse card: {exc}")

        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "div.job-card",
            "div[class*='job-card']",
            "div[class*='JobCard']",
            "div[class*='job_listing']",
            "div.job-listing",
            "div.job-item",
            "div[class*='job-item']",
            "div.card",
            "div[class*='card']",
            "a[href*='/job/']",
            "div[class*='listing']",
            "li[class*='job']",
            "article",
            "div.post",
            "div.opportunity-card",
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
        salary = self._extract_salary(card)
        experience = self._extract_experience(card)
        tags = self._extract_tags(card)
        description = self._extract_description(card)
        posted_text = self._extract_posted_date(card)
        image_url = self._extract_image_url(card)
        deadline = self._infer_deadline(posted_text)
        remote = "remote" in location.lower()
        employment_type = self._extract_labeled_text(card, "Type").lower().replace("_", "-")

        if len(description) < 20:
            description = self._fallback_description(title, organizer, location, experience, tags)

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline if deadline else "",
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "experience": experience,
            "employment_type": employment_type or "full-time",
            "remote": remote,
            "salary_currency": "INR",
            "image_url": image_url,
            "is_closed": False,
        }

    def _extract_title(self, card) -> str:
        selectors = [
            "h2 a", "h3 a", "h2", "h3",
            "a[class*='title']", "span[class*='title']",
            "div[class*='title'] a",
            "div[class*='heading'] a",
            "a[href*='/job/']",
            "[class*='job-title']",
            "[class*='JobTitle']",
            "[class*='job_name']",
            "strong a",
            "strong",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_link(self, card) -> str:
        selectors = [
            "a[href*='/job/']",
            "a[href*='/jobs/']",
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
            "[class*='company-name']",
            "[class*='CompanyName']",
            "[class*='employer']",
            "[class*='org']",
            "p[class*='org']",
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

    def _extract_salary(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Salary")
        if labeled:
            return labeled.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        selectors = [
            "[class*='salary']",
            "[class*='Salary']",
            "[class*='stipend']",
            "[class*='pay']",
            "[class*='amount']",
            "[class*='price']",
            "span[class*='money']",
            "[class*='rupee']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    text = text.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
                    return text
        return ""

    def _extract_experience(self, card) -> str:
        labeled = self._extract_labeled_text(card, "Experience")
        if labeled:
            return labeled
        selectors = [
            "[class*='experience']",
            "[class*='Experience']",
            "[class*='exp']",
            "[class*='fresher']",
            "[class*='Exp']",
            "span[class*='year']",
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
        labeled_skills = self._extract_labeled_text(card, "Skills")
        if labeled_skills:
            return [s.strip() for s in labeled_skills.split(",") if s.strip()]
        selectors = [
            "[class*='tag']",
            "[class*='skill']",
            "[class*='badge']",
            "[class*='category']",
            "[class*='tech']",
            "span[class*='label']",
            "ul li",
        ]
        seen: set[str] = set()
        tags: list[str] = []
        for sel in selectors:
            for el in card.select(sel):
                text = el.get_text(strip=True)
                if text and text.lower() not in seen and len(text) < 50:
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

    def _fallback_description(
        self,
        title: str,
        company: str,
        location: str,
        experience: str,
        tags: list[str],
    ) -> str:
        parts = [title]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"in {location}")
        if experience:
            parts.append(f"requiring {experience}")
        if tags:
            parts.append("with skills in " + ", ".join(tags[:5]))
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
