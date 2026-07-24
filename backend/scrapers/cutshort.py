import json
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class CutshortScraper(GenericScraper):
    platform_name = "CutShort"
    source_key = "cutshort"
    verticals = ["job_lateral"]
    requires_playwright = True

    BASE_URL = "https://cutshort.io"
    MAX_PAGES = 2
    MAX_ITEMS = 60

    SEARCH_QUERIES = [
        "software-engineer",
        "senior-software-engineer",
        "lead-engineer",
        "engineering-manager",
        "backend-engineer",
        "frontend-engineer",
        "data-scientist",
        "product-manager",
        "devops-engineer",
        "tech-lead",
    ]

    def scrape(self, client) -> list[dict]:
        return self._with_playwright(self._playwright_scrape)

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
        })

        all_items = []
        seen_urls = set()

        for query in self.SEARCH_QUERIES:
            if len(all_items) >= self.MAX_ITEMS:
                break

            items = self._scrape_query(page, query, seen_urls)
            all_items.extend(items)
            logger.info(f"CutShort: '{query}' -> {len(items)} items (total: {len(all_items)})")

        logger.info(f"CutShort: {len(all_items)} total lateral items")
        self._log_sample_links(all_items)
        return all_items[:self.MAX_ITEMS]

    def _scrape_query(self, page, query: str, seen_urls: set) -> list[dict]:
        search_url = f"{self.BASE_URL}/jobs?q={query}"
        logger.info(f"CutShort: fetching search page for '{query}'")

        items = []
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            if page.url.startswith((f"{self.BASE_URL}/auth", f"{self.BASE_URL}/login")):
                logger.warning(f"CutShort: authwall for '{query}'")
                return []

            try:
                page.wait_for_selector("a[href*='/job/']", timeout=15000)
            except Exception:
                logger.warning(f"CutShort: no job links for '{query}'")
                return []

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            job_links = soup.select("a[href*='/job/']")

            # Collect unique job URLs
            job_urls = []
            for a in job_links:
                href = a.get("href", "")
                if href and "/job/" in href:
                    full_url = href if href.startswith("http") else urljoin(self.BASE_URL, href)
                    if full_url not in seen_urls and full_url not in job_urls:
                        job_urls.append(full_url)

            logger.info(f"CutShort: found {len(job_urls)} unique job URLs for '{query}'")

            # Visit each job detail page
            for url in job_urls[:10]:
                try:
                    item = self._scrape_detail(page, url)
                    if item:
                        seen_urls.add(url)
                        items.append(item)
                except Exception as exc:
                    logger.debug(f"CutShort: detail scrape error {url}: {exc}")

        except ScrapeBlockedError:
            raise
        except Exception as e:
            logger.warning(f"CutShort: search error for '{query}': {e}")

        return items

    def _scrape_detail(self, page, url: str) -> dict | None:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        if page.url.startswith((f"{self.BASE_URL}/auth", f"{self.BASE_URL}/login")):
            return None

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD first
        scripts = soup.select("script[type='application/ld+json']")
        for s in scripts:
            try:
                data = json.loads(s.string or s.get_text())
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    return self._parse_jsonld(data, url)
            except (json.JSONDecodeError, TypeError):
                continue

        # Fall back to DOM parsing
        return self._parse_detail_dom(soup, url)

    def _parse_jsonld(self, data: dict, url: str) -> dict:
        title = data.get("title", "")
        description = data.get("description", "")
        if description:
            description = re.sub(r"<[^>]+>", " ", description)[:2000]

        org = data.get("hiringOrganization", {})
        company = org.get("name", "") if isinstance(org, dict) else ""

        loc_data = data.get("jobLocation", {})
        if isinstance(loc_data, list) and loc_data:
            loc_data = loc_data[0]
        location = ""
        if isinstance(loc_data, dict):
            addr = loc_data.get("address", {})
            parts = [addr.get("addressLocality", ""), addr.get("addressRegion", "")]
            location = ", ".join(p for p in parts if p)

        salary = ""
        salary_data = data.get("baseSalary", {})
        if salary_data:
            value = salary_data.get("value", {})
            min_sal = value.get("minValue")
            max_sal = value.get("maxValue")
            if min_sal and max_sal:
                salary = f"Rs.{min_sal:,.0f} - Rs.{max_sal:,.0f}/year"

        skills = data.get("skills", "")
        tags = [s.strip() for s in skills.split(",") if s.strip()] if isinstance(skills, str) else []

        exp_min, exp_max = 2, 5
        title_lower = title.lower()
        if "senior" in title_lower or "lead" in title_lower:
            exp_min, exp_max = 5, 10
        elif "manager" in title_lower or "staff" in title_lower:
            exp_min, exp_max = 5, 12
        elif "principal" in title_lower or "architect" in title_lower:
            exp_min, exp_max = 8, 15

        difficulty = self._resolve_experience_level(exp_min, exp_max, title, tags)

        return {
            "title": title,
            "type": "job",
            "link": url,
            "organizer": company,
            "description": description,
            "location": location or "India",
            "prize": salary,
            "salary_currency": "INR",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "remote": False,
            "date": "",
            "tags": tags,
            "difficulty": difficulty,
            "image_url": "",
            "is_closed": False,
        }

    def _parse_detail_dom(self, soup: BeautifulSoup, url: str) -> dict | None:
        title_el = soup.select_one("h1, h2[class*='title'], [class*='jobTitle']")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        company = ""
        for sel in ["[class*='company']", "[class*='organizer']", "[class*='employer']",
                     "a[class*='company']", "span[class*='company']"]:
            el = soup.select_one(sel)
            if el:
                company = el.get_text(strip=True)
                if company:
                    break

        location = ""
        for sel in ["[class*='location']", "[class*='locality']", "span[class*='loc']"]:
            el = soup.select_one(sel)
            if el:
                location = el.get_text(strip=True)
                if location:
                    break

        salary = ""
        for sel in ["[class*='salary']", "[class*='compensation']", "[class*='pay']", "[class*='stipend']"]:
            el = soup.select_one(sel)
            if el:
                salary = el.get_text(strip=True)
                if salary:
                    break

        tags = []
        for sel in ["[class*='skill']", "[class*='tag']", "[class*='tech']"]:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if text:
                    tags.append(text)

        description = ""
        for sel in ["[class*='description']", "[class*='about']", "div[class*='desc']"]:
            el = soup.select_one(sel)
            if el:
                description = el.get_text(strip=True)[:1000]
                if description:
                    break

        # Infer experience from title
        exp_min, exp_max = 2, 5
        title_lower = title.lower()
        if "senior" in title_lower:
            exp_min, exp_max = 5, 10
        elif "lead" in title_lower or "manager" in title_lower:
            exp_min, exp_max = 5, 12
        elif "principal" in title_lower or "architect" in title_lower or "staff" in title_lower:
            exp_min, exp_max = 8, 15
        elif "junior" in title_lower or "associate" in title_lower:
            exp_min, exp_max = 0, 2

        difficulty = self._resolve_experience_level(exp_min, exp_max, title, tags)
        remote = "remote" in (title + location).lower() or "work from home" in (title + description).lower()

        return {
            "title": title,
            "type": "job",
            "link": url,
            "organizer": company,
            "description": description,
            "location": location or "India",
            "prize": salary,
            "salary_currency": "INR",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "remote": remote,
            "date": "",
            "tags": tags[:10],
            "difficulty": difficulty,
            "image_url": "",
            "is_closed": False,
        }

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        text = posted_text.lower().strip()
        if re.search(r"today|just now|just posted|moments", text):
            return (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        if "yesterday" in text:
            return (datetime.now(timezone.utc) + timedelta(days=29)).strftime("%Y-%m-%d")
        match = re.search(r"(\d+)\s*(day|week|month)", text)
        if not match:
            return ""
        count = int(match.group(1))
        unit = match.group(2)
        days_ago = count * (30 if "month" in unit else 7 if "week" in unit else 1)
        days_remaining = max(0, 30 - days_ago)
        return (datetime.now(timezone.utc) + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
