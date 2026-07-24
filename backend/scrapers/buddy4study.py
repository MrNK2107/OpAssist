import logging
import re
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class Buddy4StudyScraper(GenericScraper):
    """Buddy4Study scholarships scraper."""

    platform_name = "Buddy4Study"
    source_key = "buddy4study"
    BASE_URL = "https://www.buddy4study.com"
    LISTING_URL = f"{BASE_URL}/scholarships"
    API_URL = "https://api.buddy4study.com/api/v1.0/ssms/scholarshipResult"
    MAX_PAGES = 2
    PUBLIC_TOKEN_RE = re.compile(r'ey="(eyJ[^"]+)"')

    def scrape(self, client=None) -> list[dict]:
        return []

    def run(self) -> list[dict]:
        self.logger.info(f"Starting {self.platform_name} scraper")
        try:
            items = self._scrape_api()
            if items:
                self.logger.info(f"Completed {self.platform_name} API scraper: {len(items)} items")
                return items
        except Exception as exc:
            self.logger.warning(f"Buddy4Study API failed, falling back to Playwright: {exc}")

        return self._scrape_playwright()

    def _scrape_api(self) -> list[dict]:
        token = self._fetch_public_token()
        if not token:
            self.logger.warning("Buddy4Study: public API token not found in client bundle")
            return []

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {token}",
            "Origin": self.BASE_URL,
            "Referer": self.LISTING_URL,
            "User-Agent": self._get_random_user_agent(),
        }

        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            response = client.get(self.API_URL, params={"page": 0, "size": 50})
            if not response.is_success:
                self.logger.warning(f"Buddy4Study API: HTTP {response.status_code}")
                return []
            data = response.json()

            raw_items = data.get("data") if isinstance(data, dict) else []
            if not isinstance(raw_items, list):
                return []

            items: list[dict] = []
            seen_urls: set[str] = set()
            for raw in raw_items:
                detail = self._fetch_detail(client, raw.get("slug"))
                item = self._parse_api_item(raw, detail)
                if item and item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    items.append(item)
        return items

    def _fetch_detail(self, client: httpx.Client, slug: str | None) -> dict:
        if not slug:
            return {}
        try:
            response = client.get(f"https://api.buddy4study.com/api/v1.0/ssms/scholarship/{slug}")
            if response.is_success:
                data = response.json()
                return data if isinstance(data, dict) else {}
        except Exception as exc:
            self.logger.debug(f"Buddy4Study detail failed for {slug}: {exc}")
        return {}

    def _fetch_public_token(self) -> str:
        headers = {"User-Agent": self._get_random_user_agent()}
        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            page = client.get(self.LISTING_URL)
            if not page.is_success:
                return ""
            soup = BeautifulSoup(page.text, "html.parser")
            scripts = [
                script.get("src")
                for script in soup.find_all("script", src=True)
                if script.get("src") and "/_next/static/chunks/pages/_app-" in script.get("src")
            ]
            for src in scripts:
                script_url = src if src.startswith("http") else f"{self.BASE_URL}{src}"
                script = client.get(script_url)
                if not script.is_success:
                    continue
                match = self.PUBLIC_TOKEN_RE.search(script.text)
                if match:
                    return match.group(1)
        return ""

    def _parse_api_item(self, raw: dict, detail: dict | None = None) -> dict | None:
        if not isinstance(raw, dict):
            return None
        detail = detail or {}
        title = (raw.get("title") or "").strip()
        slug = (raw.get("slug") or "").strip()
        if not title or not slug:
            return None

        link = f"{self.BASE_URL}/scholarship/{slug}"
        prize = raw.get("purposeAward") or raw.get("awardAmount") or ""
        deadline = self._parse_deadline_text(str(
            detail.get("deadlineDate")
            or detail.get("onlineDeadline")
            or detail.get("offlineDeadline")
            or ""
        ))
        publish_date = self._parse_deadline_text(str(raw.get("publishDate") or ""))
        description_parts = [
            raw.get("applicableFor") or "",
            f"Scholars: {raw.get('scholars')}" if raw.get("scholars") else "",
            f"Published: {publish_date}" if publish_date else "",
        ]
        description = " | ".join(part for part in description_parts if part)[:1000]
        tags = ["scholarship", "india"]
        applicable_for = (raw.get("applicableFor") or "").lower()
        for tag in ("girls", "engineering", "graduation", "post-graduation", "class 12"):
            if tag in applicable_for:
                tags.append(tag)

        item = self._build_item(title, link, str(prize or ""), deadline)
        if self._is_expired(deadline):
            return None
        item.update({
            "description": description,
            "tags": tags,
            "image_url": detail.get("logoFid") or raw.get("logo") or "",
        })
        return item

    def _scrape_playwright(self) -> list[dict]:
        self.logger.info(f"Starting {self.platform_name} scraper (Playwright fallback)")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.logger.error("Buddy4Study: playwright not installed")
            return []

        all_items: list[dict] = []
        seen_urls: set[str] = set()

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-IN",
                )
                page = context.new_page()

                for pnum in range(1, self.MAX_PAGES + 1):
                    url = f"{self.LISTING_URL}?page={pnum}" if pnum > 1 else self.LISTING_URL
                    self.logger.info(f"Buddy4Study: fetching page {pnum}: {url}")

                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_load_state("load", timeout=10000)
                        time.sleep(2)
                        items = self._parse_listing_page(page.content())
                        for item in items:
                            if item["link"] not in seen_urls:
                                seen_urls.add(item["link"])
                                all_items.append(item)
                        if not items:
                            self.logger.info(f"Buddy4Study: no items on page {pnum}, stopping")
                            break
                    except Exception as exc:
                        self.logger.warning(f"Buddy4Study page {pnum} error: {exc}")
                        break

                browser.close()
        except Exception as exc:
            self.logger.error(f"Buddy4Study Playwright failed: {exc}", exc_info=True)

        for item in all_items:
            raw = item.get("prize")
            if raw:
                item["prize"] = self._sanitize_prize(raw)

        self.logger.info(f"Completed {self.platform_name} scraper: {len(all_items)} items")
        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("a[href*='/scholarship/']")
        if not cards:
            cards = soup.find_all("a", href=re.compile(r"/scholarship/", re.I))

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Buddy4Study: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        href = card.get("href", "")
        if not href or "/scholarship/" not in href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        title = ""
        h4 = card.find("h4")
        if h4:
            title = h4.get_text(strip=True)
        if not title:
            title = card.get_text(strip=True)[:200]
        if not title:
            return None

        deadline = ""
        for p in card.select("p"):
            parsed = self._parse_deadline_text(p.get_text(strip=True))
            if parsed:
                deadline = parsed
                break

        prize = ""
        for span in card.select("span"):
            text = span.get_text(strip=True)
            if any(kw in text.lower() for kw in ["rs.", "inr", "fee waiver", "stipend", "award", "scholarship amount"]):
                prize = text[:100]
                break

        return self._build_item(title, link, prize, deadline)

    def _build_item(self, title: str, link: str, prize: str = "", deadline: str = "") -> dict:
        return {
            "title": title,
            "type": "scholarship",
            "link": link,
            "organizer": "Buddy4Study",
            "description": "",
            "location": "India",
            "prize": self._sanitize_prize(prize),
            "date": deadline,
            "tags": [],
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }

    def _is_expired(self, date_text: str) -> bool:
        if not date_text:
            return False
        try:
            deadline = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            return False
        return deadline < datetime.now(timezone.utc).date()

    def _parse_deadline_text(self, text: str) -> str:
        if not text:
            return ""
        for fmt in ["%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(text.strip(), fmt).replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return ""
