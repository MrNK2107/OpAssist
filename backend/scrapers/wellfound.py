import json
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class WellfoundScraper(GenericScraper):
    platform_name = "Wellfound"
    source_key = "wellfound"
    verticals = ["job_lateral"]
    requires_playwright = True

    BASE_URL = "https://wellfound.com"
    MAX_PAGES = 3

    ROLE_QUERIES = [
        "software-engineer",
        "backend-engineer",
        "frontend-engineer",
        "fullstack-engineer",
        "data-scientist",
        "product-manager",
        "devops-engineer",
        "machine-learning-engineer",
        "technical-lead",
        "engineering-manager",
    ]

    EXPERIENCE_KEYWORDS = {
        "senior": (5, 10),
        "staff": (8, 15),
        "lead": (5, 10),
        "principal": (10, 15),
        "manager": (5, 12),
        "mid": (2, 5),
        "software engineer ii": (2, 5),
        "software engineer iii": (5, 8),
    }

    def scrape(self, client: httpx.Client) -> list[dict]:
        client.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"{self.BASE_URL}/",
        })

        try:
            items = self._fetch_httpx(client)
            if items:
                logger.info(f"Wellfound: {len(items)} items via httpx")
                return items
        except ScrapeBlockedError:
            logger.info("Wellfound: httpx blocked (Cloudflare/DataDome), falling back to Playwright")

        return self._with_playwright(self._playwright_scrape)

    def _fetch_httpx(self, client: httpx.Client) -> list[dict]:
        all_items = []
        seen_urls = set()

        for role in self.ROLE_QUERIES:
            for page in range(1, self.MAX_PAGES + 1):
                url = f"{self.BASE_URL}/role/l/{role}/india?page={page}"
                logger.info(f"Wellfound httpx: {role} page {page}")

                try:
                    response = client.get(url, timeout=30)
                    if response.status_code == 403:
                        raise ScrapeBlockedError(source=self.source_key, status_code=403)
                    if not response.is_success:
                        logger.warning(f"Wellfound httpx {role} page {page}: HTTP {response.status_code}")
                        break

                    items = self._parse_listing_page(response.text, role)
                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    if not items:
                        break

                except ScrapeBlockedError:
                    raise
                except Exception as exc:
                    logger.warning(f"Wellfound httpx {role} page {page} error: {exc}")
                    break

        return all_items

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

        for role in self.ROLE_QUERIES:
            for page_num in range(1, self.MAX_PAGES + 1):
                url = f"{self.BASE_URL}/role/l/{role}/india?page={page_num}"
                logger.info(f"Wellfound PW: {role} page {page_num}")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3000 + page_num * 500)

                    if page.url.startswith(("https://wellfound.com/auth", "https://auth.wellfound.com")):
                        logger.warning(f"Wellfound: authwall on role {role}")
                        continue

                    try:
                        page.wait_for_selector(
                            "a[href*='/company/'], div[class*='job'], li[class*='job'], article[class*='job']",
                            timeout=15000,
                        )
                    except Exception:
                        logger.warning(f"Wellfound PW: no jobs for {role} page {page_num}")
                        break

                    page.wait_for_timeout(2000)

                    html = page.content()
                    items = self._parse_listing_page(html, role)

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                    logger.info(f"Wellfound PW: {role} page {page_num} -> {len(items)} items")
                    if not items:
                        break

                except ScrapeBlockedError:
                    raise
                except Exception as e:
                    logger.warning(f"Wellfound PW error {role} page {page_num}: {e}")
                    break

        logger.info(f"Wellfound: {len(all_items)} total lateral items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing_page(self, html: str, role: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        jsonld_scripts = soup.select('script[type="application/ld+json"]')
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string or script.get_text())
                if isinstance(data, list):
                    items = []
                    for entry in data:
                        if isinstance(entry, dict) and entry.get("@type") in ("ItemList", "SearchResultsPage"):
                            for item in entry.get("itemListElement", []):
                                parsed = self._parse_jsonld_item(item, role)
                                if parsed:
                                    items.append(parsed)
                    if items:
                        return items
            except (json.JSONDecodeError, TypeError):
                continue

        cards = soup.select(
            "a[href*='/company/'], div[class*='styles_jobCard'], "
            "li[class*='job-card'], article[class*='job'], div[class*='job-listing']"
        )
        items = []
        for card in cards:
            try:
                item = self._parse_card(card, role)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Wellfound card parse error: {exc}")

        return items

    def _parse_jsonld_item(self, item: dict, role: str) -> dict | None:
        job = item if isinstance(item, dict) else item.get("item", {})
        title = job.get("name") or job.get("title") or ""
        if not title:
            return None

        url = job.get("url") or ""
        if not url:
            return None

        company = ""
        hiring_org = job.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name", "")

        location = ""
        loc_data = job.get("jobLocation", {})
        if isinstance(loc_data, dict):
            addr = loc_data.get("address", {})
            if isinstance(addr, dict):
                location = ", ".join(p for p in [addr.get("addressLocality", ""), addr.get("addressRegion", "")] if p)

        description = job.get("description", "")
        if description:
            description = re.sub(r"<[^>]+>", " ", description)[:2000]

        salary = ""
        salary_data = job.get("baseSalary", {})
        if isinstance(salary_data, dict):
            value = salary_data.get("value", {})
            if isinstance(value, dict):
                min_sal = value.get("minValue")
                max_sal = value.get("maxValue")
                if min_sal and max_sal:
                    salary = f"${min_sal:,.0f} - ${max_sal:,.0f}/year"
                elif min_sal:
                    salary = f"${min_sal:,.0f}/year"
                elif max_sal:
                    salary = f"${max_sal:,.0f}/year"

        tags = [role.replace("-", " ").title()]
        if job.get("employmentType"):
            tags.append(job["employmentType"])

        _, exp_min, exp_max = self._infer_experience(title)

        difficulty = self._resolve_experience_level(exp_min, exp_max, title, tags)

        return {
            "title": title,
            "type": "job",
            "link": url,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "salary_currency": "USD",
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

    def _parse_card(self, card, role: str) -> dict | None:
        title_el = card.select_one(
            "h2, h3, h4, [class*='title'], [class*='jobTitle'], [class*='position'], "
            "a[href*='/company/'] strong, a[href*='/role/']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title = card.get("title", "") or card.get_text(strip=True)[:100]
        if not title:
            return None

        href = ""
        link_tag = card if card.name == "a" else card.select_one("a[href*='/company/'], a[href*='/role/']")
        if link_tag:
            href = link_tag.get("href", "")
        if not href:
            return None
        link = href if href.startswith("http") else urljoin(self.BASE_URL, href)

        company_el = card.select_one(
            "span[class*='company'], [class*='employer'], [class*='org-name'], "
            "a[class*='company'], div[class*='company']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "span[class*='location'], span[class*='loc'], div[class*='location']"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        salary_el = card.select_one(
            "span[class*='salary'], span[class*='pay'], span[class*='comp'], "
            "[class*='compensation'], [class*='equity']"
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        tags_els = card.select(
            "span[class*='skill'], span[class*='tag'], [class*='badge'], "
            "span[class*='tech-stack'] span"
        )
        tags = [s.get_text(strip=True) for s in tags_els if s.get_text(strip=True)]
        if not tags:
            tags = [role.replace("-", " ").title()]

        desc_el = card.select_one(
            "p[class*='description'], div[class*='desc'], [class*='snippet']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        equity_el = card.select_one("span[class*='equity'], [class*='stock']")
        if equity_el and salary:
            salary += f" + {equity_el.get_text(strip=True)}"

        _, exp_min, exp_max = self._infer_experience(title)

        difficulty = self._resolve_experience_level(exp_min, exp_max, title, tags)

        img_el = card.select_one("img[src*='logo'], img[class*='logo']")
        image_url = img_el.get("src", "") if img_el else ""

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "salary_currency": "USD",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "remote": "remote" in (title + location).lower(),
            "date": "",
            "tags": tags,
            "difficulty": difficulty,
            "image_url": image_url,
            "is_closed": False,
        }

    def _infer_experience(self, title: str) -> tuple[str, int | None, int | None]:
        title_lower = title.lower()
        for keyword, (exp_min, exp_max) in self.EXPERIENCE_KEYWORDS.items():
            if keyword in title_lower:
                return keyword, exp_min, exp_max

        if any(kw in title_lower for kw in ("fresher", "entry", "junior", "graduate", "trainee", "intern")):
            return "entry", 0, 1

        return "mid", 2, 5

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        text = posted_text.lower().strip()

        if re.search(r"today|just now|just posted|recently", text):
            return (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        match = re.search(r"(\d+)\s*(day|week|month)", text)
        if not match:
            return ""

        count = int(match.group(1))
        unit = match.group(2)
        if "month" in unit:
            days_ago = count * 30
        elif "week" in unit:
            days_ago = count * 7
        else:
            days_ago = count

        days_remaining = max(0, 30 - days_ago)
        return (datetime.now(timezone.utc) + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
