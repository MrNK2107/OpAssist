import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class ShineScraper(GenericScraper):
    platform_name = "Shine"
    source_key = "shine"
    verticals = ["job"]
    requires_playwright = True
    BASE_URL = "https://www.shine.com"
    LISTING_URLS = [
        f"{BASE_URL}/job-search/fresher-jobs",
    ]
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.shine.com/",
        })

        blocked = False
        for base_url in self.LISTING_URLS:
            try:
                items = self._fetch_listings(client, base_url)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
            except ScrapeBlockedError:
                blocked = True
                break
            except Exception:
                continue

        if blocked or not all_items:
            if blocked:
                logger.info("Shine: httpx blocked (403), falling back to Playwright")
            else:
                logger.info("Shine: no items from httpx, trying Playwright fallback")
            return self._with_playwright(self._playwright_scrape)

        logger.info(f"Shine: {len(all_items)} total items")
        return all_items

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Shine (Playwright): starting stealth scrape")
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
        })

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for base_url in self.LISTING_URLS[:2]:
            for page_num in range(1, self.MAX_PAGES + 1):
                url = f"{base_url}?page={page_num}" if page_num > 1 else base_url
                logger.info(f"Shine (Playwright): fetching {url}")
                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    page.wait_for_timeout(3000)
                    html = page.content()
                    items = self._parse_listing_page(html)
                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)
                    if not items:
                        break
                    logger.info(f"Shine (Playwright): page {page_num} -> {len(items)} items")
                except Exception as e:
                    logger.warning(f"Shine (Playwright): error on page {page_num}: {e}")
                    break

        logger.info(f"Shine (Playwright): {len(all_items)} total items")
        return all_items

    def _fetch_listings(self, client: httpx.Client, base_url: str) -> list[dict]:
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url

            logger.info(f"Shine: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(source=self.source_key, status_code=403)
                if not response.is_success:
                    logger.warning(f"Shine page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                all_items.extend(items)
                if not items:
                    break
            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"Shine page {page} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.jdbigCard[itemtype='https://schema.org/ListItem']")
        if not cards:
            cards = soup.select(
                "article.jobCard, div.job_card, div.jobCard, "
                "div[class*='job-card'], div[class*='jobCardNova_bigCard__'][itemprop='itemListElement'], "
                "li[class*='job']"
            )
        if not cards:
            cards = soup.select("[data-job-id], [id*='job_']")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Shine: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "a[class*='title'], a[class*='jobTitle'], "
            "h2 a, h2[class*='title'], h3 a, h3[class*='Title'], "
            "a[href*='/job/'], a[href*='/jobs/']"
        )
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            title_el = card.select_one("a[href*='shine.com']")
            title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        href = title_el.get("href", "") if title_el else ""
        if not href:
            link_el = card.select_one("a[href*='shine.com']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        company_el = card.select_one(
            "span[class*='company'], a[class*='company'], "
            "span[class*='Company'], span[class*='TitleName'], "
            "span[class*='comp'], p[class*='org']"
        )
        company = company_el.get("title", "").strip() if company_el else ""
        if not company and company_el:
            company = company_el.get_text(" ", strip=True)

        location_el = card.select_one(
            "span[class*='location'], span[class*='loc'], "
            "p[class*='location'], [class*='Location'] span, "
            "[class*='CenterListLoc'] span, [class*='place']"
        )
        location = location_el.get_text(" ", strip=True) if location_el else ""

        salary_el = card.select_one(
            "span[class*='salary'], span[class*='sal'], "
            "[class*='pay'], [class*='package']"
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        experience_el = card.select_one(
            "span[class*='exp'], [class*='experience'], "
            "span[class*='year']"
        )
        experience = experience_el.get_text(strip=True) if experience_el else ""
        detail_spans = [el.get_text(" ", strip=True) for el in card.select("[class*='CenterListExp']")]
        if detail_spans:
            experience = experience or detail_spans[0]
            if len(detail_spans) > 1 and not salary:
                salary = detail_spans[1]

        desc_el = card.select_one(
            "p[class*='desc'], div[class*='desc'], "
            "span[class*='desc'], [class*='description']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        skills_el = card.select_one(
            "div[class*='skill'], ul[class*='skill'], "
            "[class*='tags'], [class*='keyskill']"
        )
        skills = [
            s.get_text(strip=True)
            for s in skills_el.select("span, li, a") if s.get_text(strip=True)
        ] if skills_el else []

        posted_el = card.select_one(
            "span[class*='date'], span[class*='time'], "
            "[class*='posted'], [class*='days']"
        )
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        deadline = self._infer_deadline(posted_text)

        tags = [s for s in [experience] if s] + skills
        if not description:
            parts = [title]
            if company:
                parts.append(f"at {company}")
            if location:
                parts.append(f"in {location}")
            if salary:
                parts.append(f"with salary {salary}")
            description = " ".join(parts) + "."

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "employment_type": "full-time",
            "date": deadline,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": "",
            "is_closed": False,
        }

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
