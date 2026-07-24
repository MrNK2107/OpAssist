import json
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class ApnaScraper(GenericScraper):
    platform_name = "Apna"
    source_key = "apna"
    verticals = ["job"]
    requires_playwright = True

    BASE_URL = "https://apna.co"
    JOBS_URL = "https://apna.co/jobs/fresher-jobs"
    MAX_JOBS = 50
    SCROLL_PAUSE_SEC = 2.0

    def scrape(self, client: httpx.Client) -> list[dict]:
        items = self._http_scrape(client)
        if items:
            return items
        return self._with_playwright(self._playwright_scrape)

    def _http_scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, 3):
            url = self.JOBS_URL if page == 1 else f"{self.JOBS_URL}?page={page}"
            response = client.get(url, timeout=30)
            if not response.is_success:
                logger.warning(f"Apna page {page}: HTTP {response.status_code}")
                break
            items = self._parse_dom(response.text)
            if not items:
                break
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)
            if len(all_items) >= self.MAX_JOBS:
                break

        logger.info(f"Apna: HTTP scrape got {len(all_items)} items")
        return all_items[:self.MAX_JOBS]

    def _playwright_scrape(self, page) -> list[dict]:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://apna.co/",
        })

        logger.info("Apna: navigating to jobs listing page")

        api_items = []

        try:
            api_items = self._try_api_intercept(page)
            if len(api_items) >= self.MAX_JOBS:
                logger.info(f"Apna: got {len(api_items)} items via API intercept, skipping DOM scrape")
                return api_items[:self.MAX_JOBS]
        except Exception as e:
            logger.info(f"Apna: API intercept failed ({e}), falling back to DOM scrape")

        try:
            dom_items = self._dom_scrape(page)
            all_items = api_items + dom_items
            seen = set()
            deduped = []
            for item in all_items:
                key = item.get("link", "") or item.get("title", "")
                if key not in seen:
                    seen.add(key)
                    deduped.append(item)
            logger.info(f"Apna: {len(deduped)} total items (API: {len(api_items)}, DOM: {len(dom_items)})")
            return deduped[:self.MAX_JOBS]
        except ScrapeBlockedError:
            raise
        except Exception as e:
            logger.error(f"Apna: DOM scrape failed after API intercept: {e}")
            return api_items

    # ------------------------------------------------------------------
    # API Intercept (reverse-engineered XHR)
    # ------------------------------------------------------------------

    def _try_api_intercept(self, page) -> list[dict]:
        responses = []

        def handle_response(response):
            url = response.url
            if "/api/" in url or "/graphql" in url or "/search" in url or "/jobs" in url:
                if response.status == 200:
                    try:
                        body = response.json()
                        responses.append(body)
                    except Exception:
                        pass

        page.on("response", handle_response)

        page.goto(self.JOBS_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        items = []
        for body in responses:
            parsed = self._parse_api_response(body)
            items.extend(parsed)

        page.remove_listener("response", handle_response)
        return items

    def _parse_api_response(self, body) -> list[dict]:
        items = []

        if isinstance(body, list):
            data = body
        elif isinstance(body, dict):
            data = body.get("data") or body.get("results") or body.get("jobs") or []
            if isinstance(data, dict):
                data = data.get("results") or data.get("jobs") or data.get("items") or []
        else:
            data = []

        if not isinstance(data, list):
            return items

        for entry in data:
            if isinstance(entry, dict):
                item = self._parse_api_job(entry)
                if item:
                    items.append(item)

        return items

    def _parse_api_job(self, entry: dict) -> dict | None:
        title = entry.get("title") or entry.get("jobTitle") or entry.get("name", "")
        if not title:
            return None

        link = ""
        slug = entry.get("slug") or entry.get("jobSlug") or ""
        job_id = entry.get("id") or entry.get("jobId") or ""
        if slug:
            link = urljoin(self.BASE_URL, f"/jobs/{slug}")
        elif job_id:
            link = urljoin(self.BASE_URL, f"/jobs/{job_id}")

        company = entry.get("companyName") or entry.get("company") or entry.get("organizer", "")
        location = entry.get("location") or entry.get("jobLocation") or ""
        salary = entry.get("salary") or entry.get("minSalary") or ""
        if salary and entry.get("maxSalary"):
            salary = f"{salary} - {entry['maxSalary']}"

        skills = entry.get("skills") or entry.get("tags") or entry.get("keySkills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        tags = skills if isinstance(skills, list) else []

        description = entry.get("description") or entry.get("jobDescription") or entry.get("about", "")

        posted_raw = entry.get("postedDate") or entry.get("postedAt") or entry.get("createdAt", "")
        date = self._parse_date(posted_raw)

        company_logo = entry.get("companyLogo") or entry.get("logo") or entry.get("imageUrl", "")

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "location": location,
            "prize": salary,
            "description": description[:2000] if description else "",
            "date": date,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": company_logo,
            "is_closed": False,
        }

    # ------------------------------------------------------------------
    # DOM-based scrape (scroll + parse)
    # ------------------------------------------------------------------

    def _dom_scrape(self, page) -> list[dict]:
        logger.info("Apna: starting DOM-based scrape with infinite scroll")

        page.goto(self.JOBS_URL, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_selector("div[class*='card'], div[class*='job'], a[href*='/jobs/']", timeout=20000)
        except Exception:
            if self._is_auth_page(page):
                logger.warning("Apna: authwall detected, gracefully degrading")
                return []
            logger.warning("Apna: no job cards found on page")
            return []

        if self._is_auth_page(page):
            logger.warning("Apna: authwall detected after navigation, degrading")
            return []

        self._scroll_to_load(page)
        page.wait_for_timeout(3000)

        html = page.content()
        items = self._parse_dom(html)

        logger.info(f"Apna: DOM scrape got {len(items)} items")
        self._log_sample_links(items)
        return items

    def _scroll_to_load(self, page) -> None:
        for attempt in range(10):
            current_count = page.evaluate("document.querySelectorAll('[class*=\"card\"], [class*=\"job\"]').length")
            if current_count >= self.MAX_JOBS:
                logger.info(f"Apna: reached {current_count} job cards, stopping scroll")
                break

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(int(self.SCROLL_PAUSE_SEC * 1000))

            new_count = page.evaluate("document.querySelectorAll('[class*=\"card\"], [class*=\"job\"]').length")
            logger.info(f"Apna: scroll {attempt + 1}: {current_count} -> {new_count} cards")
            if new_count <= current_count:
                logger.info("Apna: no new cards loaded after scroll, stopping")
                break

    def _is_auth_page(self, page) -> bool:
        url = page.url.lower()
        text = (page.inner_text("body") or "").lower()

        auth_signals = [
            "authwall", "signin", "login", "sign-in", "log-in",
            "create account", "phone number", "verify",
        ]
        if any(signal in url for signal in ["authwall", "login", "signin"]):
            return True
        if any(signal in text for signal in auth_signals):
            if any(word in text for word in ["continue", "get started", "enter"]):
                return False
            return "login" in text or "sign in" in text or "create account" in text
        return False

    def _parse_dom(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select(
            "a[data-testid='job-card'], a[href*='/job/'], a[href*='/jobs/'], "
            "div[class*='card'], div[class*='job-card'], "
            "div[class*='JobCard'], div[class*='listing-card']"
        )

        items = []
        seen_urls = set()

        for card in cards:
            try:
                item = self._parse_card(card)
                if item and item.get("link") and item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Apna: card parse error: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one(
            "h2, h3, h4, [class*='title'], [class*='jobTitle'], "
            "[class*='heading'], [class*='name']"
        )
        title = title_el.get_text(" ", strip=True).strip(" |") if title_el else ""
        if not title:
            return None

        href = ""
        link_tag = card if card.name == "a" else card.select_one("a[href*='/job/'], a[href*='/jobs/']")
        if link_tag:
            href = link_tag.get("href", "")
        if not href:
            return None
        link = href if href.startswith("http") else urljoin(self.BASE_URL, href)

        if card.get("data-testid") == "job-card":
            return self._parse_current_job_card(card, title, link)

        company_el = card.select_one(
            "[class*='company'], [class*='organizer'], [class*='employer'], "
            "[class*='org']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "[class*='location'], [class*='place'], [class*='city'], "
            "[class*='locality']"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        salary_el = card.select_one(
            "[class*='salary'], [class*='stipend'], [class*='pay'], "
            "[class*='compensation']"
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        skills_els = card.select(
            "[class*='skill'], [class*='tag'], [class*='tech'], "
            "[class*='keyword']"
        )
        tags = [s.get_text(strip=True) for s in skills_els if s.get_text(strip=True)]

        desc_el = card.select_one(
            "[class*='description'], [class*='desc'], [class*='about'], "
            "[class*='summary']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        posted_el = card.select_one(
            "[class*='posted'], [class*='date'], [class*='time'], "
            "[class*='ago'], time"
        )
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        date = self._parse_date(posted_text)

        logo_el = card.select_one("img[src*='logo'], img[class*='logo'], img[alt*='logo']")
        image_url = logo_el.get("src", "") if logo_el else ""

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "location": location,
            "prize": salary,
            "description": description,
            "date": date,
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": image_url,
            "is_closed": False,
        }

    def _parse_current_job_card(self, card, title: str, link: str) -> dict:
        spans = [span.get_text(" ", strip=True) for span in card.select("span")]
        spans = [span for span in spans if span]

        company = spans[0] if len(spans) > 0 else ""
        location = spans[1] if len(spans) > 1 else ""
        salary = spans[2] if len(spans) > 2 else ""
        badges = spans[3:] if len(spans) > 3 else []

        employment_type = ""
        for badge in badges:
            if "full time" in badge.lower():
                employment_type = "full-time"
            elif "part time" in badge.lower():
                employment_type = "part-time"
        exp_min, exp_max = self._parse_experience_badges(badges)
        remote = any("work from home" in badge.lower() for badge in badges) or "remote" in location.lower()
        logo_el = card.select_one("img[alt]")
        image_url = logo_el.get("src", "") if logo_el else ""

        tags = [badge for badge in badges if not badge.lower().startswith("min.")]
        description = " | ".join(tags)[:500]

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "location": location,
            "prize": salary.replace("\u20b9", "Rs.").replace("\u20a8", "Rs."),
            "description": description,
            "date": "",
            "tags": tags,
            "difficulty": self._resolve_experience_level(exp_min, exp_max, title, tags),
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": employment_type or None,
            "remote": remote,
            "salary_currency": "INR",
            "image_url": image_url,
            "is_closed": False,
        }

    def _parse_experience_badges(self, badges: list[str]) -> tuple[int | None, int | None]:
        for badge in badges:
            match = re.search(r"min\.\s*(\d+)\s*years?", badge, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                return years, None
            if re.search(r"fresher|no experience", badge, re.IGNORECASE):
                return 0, 0
        return None, None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_date(self, raw: str) -> str:
        if not raw:
            return ""

        if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
            return raw[:10]

        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

        text = raw.lower().strip()

        if "today" in text or "just now" in text:
            return (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*(day|week|month|hour|minute)", text)
        if match:
            count = int(match.group(1))
            unit = match.group(2)
            if "month" in unit:
                days_ago = count * 30
            elif "week" in unit:
                days_ago = count * 7
            elif "hour" in unit or "minute" in unit:
                days_ago = 0
            else:
                days_ago = count
            days_remaining = max(0, 30 - days_ago)
            return (datetime.now(timezone.utc) + timedelta(days=days_remaining)).strftime("%Y-%m-%d")

        return ""
