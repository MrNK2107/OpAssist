import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class InstahyreScraper(GenericScraper):
    platform_name = "Instahyre"
    source_key = "instahyre"
    verticals = ["job"]
    requires_playwright = True

    BASE_URL = "https://www.instahyre.com"
    LISTING_URL = f"{BASE_URL}/search-jobs"
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"{self.BASE_URL}/",
        })

        try:
            items = self._fetch_listings_httpx(client)
            if items:
                logger.info(f"Instahyre: {len(items)} items via httpx")
                return items
        except ScrapeBlockedError:
            logger.info("Instahyre: httpx blocked (Cloudflare), falling back to Playwright")

        return self._with_playwright(self._playwright_scrape)

    def _fetch_listings_httpx(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self.LISTING_URL if page == 1 else f"{self.LISTING_URL}?page={page}"
            logger.info(f"Instahyre (httpx): page {page} -> {url}")

            response = client.get(url, timeout=30)
            if response.status_code == 403:
                raise ScrapeBlockedError(source=self.source_key, status_code=403)
            if not response.is_success:
                logger.warning(f"Instahyre page {page}: HTTP {response.status_code}")
                break

            items = self._parse_listing_page(response.text)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)

            if not items:
                break

        return all_items

    def _playwright_scrape(self, page) -> list[dict]:
        logger.info("Instahyre (Playwright): starting scrape")

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
            url = self.LISTING_URL if page_num == 1 else f"{self.LISTING_URL}?page={page_num}"
            logger.info(f"Instahyre (Playwright): fetching {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                try:
                    page.wait_for_selector(
                        "div.employer-block, div[ng-repeat*='opportunities']",
                        timeout=20000,
                    )
                except Exception:
                    logger.warning(f"Instahyre (Playwright): no job cards on {url}")
                    break

                page.wait_for_timeout(3000)

                self._scroll_for_lazy_load(page)

                html = page.content()
                items = self._parse_listing_page(html)

                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)

                logger.info(f"Instahyre (Playwright): page {page_num} -> {len(items)} items")

                if not items:
                    break

            except ScrapeBlockedError:
                raise
            except Exception as e:
                logger.warning(f"Instahyre (Playwright): error on page {page_num}: {e}")
                break

        logger.info(f"Instahyre (Playwright): {len(all_items)} total items")
        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.employer-block")
        if not cards:
            cards = soup.select("[ng-repeat*='opportunities']")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Instahyre: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        link_el = card.select_one("a#employer-profile-opportunity")
        if not link_el:
            link_el = card.select_one("a[ng-href*='/job-']")
        if not link_el:
            return None

        href = link_el.get("ng-href") or link_el.get("href", "")
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        name_el = card.select_one(".employer-job-name .company-name")
        full_name = name_el.get_text(strip=True) if name_el else ""

        title, company = self._split_title_company(full_name)

        if not title:
            title_el = card.select_one(".employer-details-mobile .employer-job-name .company-name")
            title = title_el.get_text(strip=True) if title_el else ""
        if not company:
            company_el = card.select_one(".employer-details-mobile .employer-company-name .company-name")
            company = company_el.get_text(strip=True) if company_el else ""

        if not title:
            return None

        location = ""
        loc_el = card.select_one(
            ".employer-locations .info span, "
            ".employer-details-mobile .employer-locations span"
        )
        if loc_el:
            loc_text = loc_el.get_text(strip=True)
            location = re.sub(r"^Job available in\s*", "", loc_text, flags=re.IGNORECASE).strip()

        skills = [
            li.get_text(strip=True)
            for li in card.select(".job-skills ul.tags li")
            if li.get_text(strip=True)
        ]

        desc_el = card.select_one(".employer-notes")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        img_el = card.select_one(".thumbnail img")
        image_url = img_el.get("src", "") if img_el else ""

        deadline = self._infer_deadline("")
        _, exp_min, exp_max = self._infer_experience(title)

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location if location else "India",
            "prize": "",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "date": deadline,
            "tags": skills,
            "difficulty": self._resolve_experience_level(exp_min, exp_max, title, skills),
            "image_url": image_url,
            "is_closed": False,
        }

    def _infer_experience(self, title: str) -> tuple[str, int | None, int | None]:
        text = title.lower()
        if any(term in text for term in ("principal", "staff", "architect", "director")):
            return "senior", 8, 15
        if any(term in text for term in ("senior", "lead", "manager")):
            return "senior", 5, 10
        if any(term in text for term in ("junior", "trainee", "fresher", "graduate", "intern")):
            return "entry", 0, 1
        return "mid", 2, 5

    @staticmethod
    def _split_title_company(full_name: str) -> tuple[str, str]:
        if " - " in full_name:
            parts = full_name.split(" - ", 1)
            return parts[1].strip(), parts[0].strip()
        return full_name, ""

    @staticmethod
    def _scroll_for_lazy_load(page) -> None:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

        text = posted_text.lower().strip()

        if text in ("24h", "24hr", "1d", "1 day ago", "today"):
            deadline = datetime.now(timezone.utc) + timedelta(days=29)
            return deadline.strftime("%Y-%m-%d")

        if "30d+" in text or "30+" in text or "30 days" in text or "month" in text:
            deadline = datetime.now(timezone.utc) + timedelta(days=1)
            return deadline.strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*(d|day|hr|h|week|wk|month|mon)", text)
        if not match:
            if "just now" in text or "moments" in text:
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            deadline = datetime.now(timezone.utc) + timedelta(days=30)
            return deadline.strftime("%Y-%m-%d")

        count = int(match.group(1))
        unit = match.group(2)

        if unit in ("month", "mon"):
            days_ago = count * 30
        elif unit in ("week", "wk"):
            days_ago = count * 7
        elif unit in ("day", "d"):
            days_ago = count
        else:
            days_ago = count

        days_remaining = max(0, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
