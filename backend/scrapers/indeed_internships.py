import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class IndeedInternshipsScraper(GenericScraper):
    platform_name = "IndeedInternships"
    source_key = "indeed_internships"
    verticals = ["internship"]
    requires_playwright = True
    BASE_URL = "https://www.indeed.com"
    SEARCH_PATH = "/internships?l=India"
    MAX_PAGES = 3

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
            items = self._fetch_listings(client)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)
        except ScrapeBlockedError:
            blocked = True

        if blocked or not all_items:
            if blocked:
                logger.info("IndeedInternships: httpx blocked (403), falling back to Playwright")
            else:
                logger.info("IndeedInternships: no items from httpx, trying Playwright fallback")
            return self._with_playwright(self._playwright_scrape)

        logger.info(f"IndeedInternships: {len(all_items)} total items")
        return all_items

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("IndeedInternships (Playwright): starting stealth scrape")

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

        for page_num in range(1, self.MAX_PAGES + 1):
            url = self._page_url(page_num)
            logger.info(f"IndeedInternships (Playwright): fetching page {page_num}: {url}")

            try:
                page.goto(url, wait_until="networkidle", timeout=60000)

                try:
                    page.wait_for_selector(
                        "[data-testid='job-card'], .job_seen_beacon, li.css-1ac2h1w, div.cardOutline",
                        timeout=20000,
                    )
                except Exception:
                    logger.warning(
                        f"IndeedInternships (Playwright): no job cards on page {page_num}"
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
                    f"IndeedInternships (Playwright): page {page_num} -> {len(items)} items"
                )
                if not items:
                    break

                page.wait_for_timeout(1000)

            except ScrapeBlockedError:
                raise
            except Exception as e:
                logger.warning(
                    f"IndeedInternships (Playwright): error on page {page_num}: {e}"
                )
                break

        logger.info(f"IndeedInternships (Playwright): {len(all_items)} total items")
        return all_items

    def _fetch_listings(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            url = self._page_url(page)
            logger.info(f"IndeedInternships: fetching page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(
                        source=self.source_key, status_code=403
                    )
                if not response.is_success:
                    logger.warning(
                        f"IndeedInternships page {page}: HTTP {response.status_code}"
                    )
                    break
                items = self._parse_listing_page(response.text)
                all_items.extend(items)
                if not items:
                    break
            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"IndeedInternships page {page} error: {exc}")
                break

        return all_items

    def _page_url(self, page_num: int) -> str:
        if page_num == 1:
            return f"{self.BASE_URL}{self.SEARCH_PATH}"
        return f"{self.BASE_URL}{self.SEARCH_PATH}&start={(page_num - 1) * 10}"

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
                logger.debug(f"IndeedInternships: failed to parse card: {exc}")

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
        for s in card.select("ul li, .tag, .skill"):
            text = s.get_text(strip=True)
            if text and text.lower() not in ("internship", "intern"):
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
            "type": "internship",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline,
            "tags": tags or ["internship"],
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }

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
