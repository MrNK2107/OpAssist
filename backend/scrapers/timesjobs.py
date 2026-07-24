import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError, infer_deadline_from_posted

logger = logging.getLogger(__name__)


class TimesJobsScraper(GenericScraper):
    platform_name = "TimesJobs"
    source_key = "timesjobs"
    verticals = ["job"]
    BASE_URL = "https://www.timesjobs.com"
    MAX_PAGES = 5
    SEARCH_QUERIES = ["Python", "Java", "Fresher", "Data Scientist", "Frontend", "Backend", "Software Engineer", "Trainee"]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.SEARCH_QUERIES:
            if len(all_items) >= 100:
                break
            for page in range(1, self.MAX_PAGES + 1):
                query_slug = query.lower().replace(" ", "-")
                url = f"{self.BASE_URL}/jobskill/{query_slug}-jobs"
                if page > 1:
                    url = f"{url}?page={page}"
                logger.info(f"TimesJobs: fetching page {page} for {query}: {url}")

                try:
                    response = client.get(url, timeout=30)
                    if response.status_code == 403:
                        raise ScrapeBlockedError(source=self.source_key, status_code=403)
                    if not response.is_success:
                        logger.warning(f"TimesJobs page {page}: HTTP {response.status_code}")
                        break

                    items = self._parse_listing_page(response.text)
                    if not items:
                        logger.info(f"TimesJobs: no items on page {page} for {query}, stopping pagination")
                        break

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(f"TimesJobs: page {page} for {query} -> {len(items)} items")
                except ScrapeBlockedError:
                    raise
                except Exception as exc:
                    logger.warning(f"TimesJobs page {page} for {query} error: {exc}")
                    break

        logger.info(f"TimesJobs: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

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
                logger.debug(f"TimesJobs: failed to parse card: {exc}")
        return items

    def _find_cards(self, soup: BeautifulSoup) -> list:
        selectors = [
            "article.job-card",
            "li[class*='job-result']",
            "div.job-bx",
            "div.job-card",
            "div[class*='job-card']",
            "div[class*='job-listing']",
            "div.job_row",
            "li[class*='job-li']",
            "div[class*='job-result']",
            "article",
            "div.card",
            "div.listing-card",
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

        company = self._extract_company(card)
        location = self._extract_location(card)
        salary = self._extract_salary(card)
        tags = self._extract_skills(card)
        posted_text = self._extract_posted_date(card)
        description = self._extract_description(card)

        deadline = infer_deadline_from_posted(posted_text)
        remote = "remote" in location.lower()

        if not description:
            description = self._build_description(title, company, location, tags)

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description[:500],
            "location": location,
            "prize": salary.replace("\u20b9", "Rs.").replace("\u20a8", "Rs. "),
            "date": deadline,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": "",
            "is_closed": False,
            "employment_type": "full-time",
            "remote": remote,
            "salary_currency": "INR",
        }

    def _extract_title(self, card) -> str:
        selectors = [
            "h2 a[href*='/job-detail/']",
            "strong a[href*='/job-detail/']",
            "a[href*='/job-detail/']",
            "h2 a",
            "h3 a",
            "h2",
            "h3",
            "a[class*='title']",
            "strong",
            "div[class*='title'] a",
            "span[class*='title']",
            "a[class*='job']",
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
            "a[href*='/job-detail/']",
            "a[href*='/jobs/']",
            "a[href*='/job/']",
            "a[class*='title']",
            "h2 a",
            "h3 a",
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
        selectors = [
            "span.company-name",
            ".comp-name",
            "span[class*='company']",
            "span[class*='comp']",
            "p[class*='company']",
            "div[class*='company']",
            "[class*='company-name']",
            "[class*='org-name']",
            "span[class*='employer']",
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
            "span.location",
            ".job-location",
            "span[class*='location']",
            "span[class*='loc']",
            "li[class*='location']",
            "div[class*='location']",
            "[class*='city']",
            "[class*='place']",
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
            "span.salary",
            ".job-salary",
            "span[class*='salary']",
            "span[class*='pay']",
            "span[class*='package']",
            "span[class*='stipend']",
            "div[class*='salary']",
            "li[class*='salary']",
            "[class*='salary']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_skills(self, card) -> list[str]:
        selectors = [
            "span.skill",
            "div.skills span",
            "span[class*='skill']",
            "div[class*='skill'] span",
            "ul.skills li",
            "li[class*='skill']",
            "a[class*='skill']",
            "span[class*='tag']",
            "div[class*='tag'] span",
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
            "span.posted",
            ".date",
            ".job-posted",
            "span[class*='posted']",
            "span[class*='date']",
            "span[class*='ago']",
            "span[class*='days']",
            "li[class*='posted']",
            "[class*='posted']",
            "[class*='created']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return ""

    def _extract_description(self, card) -> str:
        selectors = [
            "p.job-description",
            ".description",
            ".job-desc",
            "div[class*='desc']",
            "p[class*='desc']",
            "div[class*='about']",
            "div[class*='summary']",
        ]
        for sel in selectors:
            el = card.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if len(text) > 20:
                    return text[:500]
        return ""

    def _build_description(self, title: str, company: str, location: str, tags: list[str]) -> str:
        parts = [title]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"in {location}")
        if tags:
            parts.append("with skills in " + ", ".join(tags[:5]))
        return " ".join(parts) + "."
