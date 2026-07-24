import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class IndeedJobsScraper(GenericScraper):
    platform_name = "IndeedJobs"
    source_key = "indeed_jobs"
    verticals = ["job"]
    requires_playwright = True
    BASE_URL = "https://in.indeed.com"
    SEARCH_PATH = "/jobs"
    MAX_PAGES = 3
    QUERY_TERMS = ["fresher", "entry level", "graduate"]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()
        blocked = False

        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"{self.BASE_URL}/",
        })

        try:
            for query in self.QUERY_TERMS:
                items = self._fetch_listings(client, query)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
        except ScrapeBlockedError:
            blocked = True

        if blocked or not all_items:
            if blocked:
                logger.info("IndeedJobs: httpx blocked (403), falling back to Playwright")
            else:
                logger.info("IndeedJobs: no items from httpx, trying Playwright fallback")
            return self._with_playwright(self._playwright_scrape)

        logger.info(f"IndeedJobs: {len(all_items)} total items")
        return all_items

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("IndeedJobs (Playwright): starting stealth scrape")

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.QUERY_TERMS:
            for page_num in range(1, self.MAX_PAGES + 1):
                url = self._page_url(query, page_num)
                logger.info(f"IndeedJobs (Playwright): fetching page {page_num} for '{query}': {url}")

                try:
                    page.goto(url, wait_until="networkidle", timeout=60000)

                    try:
                        page.wait_for_selector(
                            "[data-testid='job-card'], .job_seen_beacon, li.css-1ac2h1w, div.cardOutline",
                            timeout=20000,
                        )
                    except Exception:
                        logger.warning(
                            f"IndeedJobs (Playwright): no job cards on page {page_num} for '{query}'"
                        )
                        break

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)

                    html = page.content()
                    items = self._parse_listing_page(html)

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(
                        f"IndeedJobs (Playwright): page {page_num} for '{query}' -> {len(items)} items"
                    )
                    if not items:
                        break

                    page.wait_for_timeout(1000)

                except ScrapeBlockedError:
                    raise
                except Exception as e:
                    logger.warning(
                        f"IndeedJobs (Playwright): error on page {page_num} for '{query}': {e}"
                    )
                    break

        logger.info(f"IndeedJobs (Playwright): {len(all_items)} total items")
        return all_items

    def _fetch_listings(self, client: httpx.Client, query: str) -> list[dict]:
        all_items: list[dict] = []

        for page_num in range(1, self.MAX_PAGES + 1):
            url = self._page_url(query, page_num)
            logger.info(f"IndeedJobs: fetching page {page_num} for '{query}': {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(
                        source=self.source_key, status_code=403
                    )
                if not response.is_success:
                    logger.warning(
                        f"IndeedJobs page {page_num}: HTTP {response.status_code}"
                    )
                    break
                items = self._parse_listing_page(response.text)
                if not items:
                    break
                all_items.extend(items)
            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"IndeedJobs page {page_num} error: {exc}")
                break

        return all_items

    def _page_url(self, query: str, page_num: int) -> str:
        params = {"q": query}
        if page_num > 1:
            params["start"] = (page_num - 1) * 10
        return f"{self.BASE_URL}{self.SEARCH_PATH}?{urlencode(params)}"

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(
            "[data-testid='job-card'], .job_seen_beacon, li.css-1ac2h1w, div.cardOutline, div.job_card"
        )

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"IndeedJobs: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "h2.jobTitle a, a.jcs-JobTitle, span[id^='jobTitle'] a, "
            "a[data-testid='job-title'], a[id*='jobTitle']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            el = card.select_one("a[data-jk]")
            title = el.get_text(strip=True) if el else ""
        if not title:
            return None

        href = title_el.get("href", "") if title_el else ""
        if not href:
            el = card.select_one("a[href*='rc/clk'], a[href*='jobView']")
            href = el.get("href", "") if el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        company_el = card.select_one(
            "span.companyName, [data-testid='company-name'], "
            "span.company, a[data-testid='company-name']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "div.companyLocation, [data-testid='text-location'], "
            "span.location, div.location"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        salary_el = card.select_one(
            "div.salary-snippet-container, span.estimated-salary, "
            "div.salaryOnly, [data-testid='test-salary'], "
            "span[id*='salary'], div.salary"
        )
        salary_text = salary_el.get_text(strip=True) if salary_el else ""

        desc_el = card.select_one(
            "div.job-snippet, ul.jobCardShelfContainer, "
            "div.jobCardShelfContainer, [data-testid='job-snippet']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        tags = []
        for s in card.select(".tag, .skill, [data-testid='attribute_snippet_testid']"):
            text = s.get_text(strip=True)
            if text and self._is_clean_tag(text):
                tags.append(text)

        posted_el = card.select_one(
            "span.date, span[data-testid='job-date'], "
            "span.css-1c0e2o8, .jobCardFooter span"
        )
        posted_text = posted_el.get_text(strip=True) if posted_el else ""

        deadline = self._infer_deadline(posted_text)
        salary = self._parse_salary(salary_text) or salary_text

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline,
            "tags": tags or ["job"],
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }

    def _is_clean_tag(self, text: str) -> bool:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized or len(normalized) > 60:
            return False
        bad_fragments = (
            "view all",
            "salary search",
            "job type",
            "shift:",
            "salary:",
            "health insurance",
            "provident fund",
        )
        if any(fragment in normalized.lower() for fragment in bad_fragments):
            return False
        return not re.search(r"(?:₹|Rs\.?|INR)?\s*[\d,]+", normalized, re.IGNORECASE)

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        text = posted_text.lower().strip()

        if re.search(r"today|just now|\d+\s*hours?\s*ago", text):
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

        if "yesterday" in text:
            deadline = datetime.now(timezone.utc) + timedelta(days=29)
            return deadline.strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*\+?\s*(day|week|month)", text)
        if not match:
            return ""

        count = int(match.group(1))
        unit = match.group(2)
        days_ago = count * (30 if "month" in unit else 7 if "week" in unit else 1)
        days_remaining = max(7, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")

    def _parse_salary(self, salary_text: str) -> str:
        if not salary_text:
            return ""
        text = salary_text.strip()

        match = re.search(
            r"(?:₹|Rs\.?|INR)?\s*([\d,]+)\s*(?:-|–|to)\s*(?:₹|Rs\.?|INR)?\s*([\d,]+)"
            r"\s*(?:/|\b)(month|year|hr|hour|week|day|annum|yr)",
            text, re.IGNORECASE,
        )
        if match:
            lo = match.group(1).replace(",", "")
            hi = match.group(2).replace(",", "")
            period = match.group(3).lower()
            suffix = {"month": "/mo", "year": "/yr", "annum": "/yr", "yr": "/yr",
                      "hr": "/hr", "hour": "/hr", "week": "/wk", "day": "/day"}.get(period, "")
            return f"₹{lo} - ₹{hi}{suffix}"

        match = re.search(
            r"(?:₹|Rs\.?|INR)?\s*([\d,]+)\s*(?:/|\b)(month|year|hr|hour|week|day|annum|yr)",
            text, re.IGNORECASE,
        )
        if match:
            amt = match.group(1).replace(",", "")
            period = match.group(2).lower()
            suffix = {"month": "/mo", "year": "/yr", "annum": "/yr", "yr": "/yr",
                      "hr": "/hr", "hour": "/hr", "week": "/wk", "day": "/day"}.get(period, "")
            return f"₹{amt}{suffix}"

        return text
