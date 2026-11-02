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
    MAX_PAGES = 1

    SEARCH_URLS = [
        f"{BASE_URL}/jobs?location=india",
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

        return self._with_playwright(self._playwright_scrape)

    def _playwright_scrape(self, page) -> list[dict]:
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            window.chrome = { runtime: {} };
        """)

        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        all_items = []
        seen_urls = set()

        for base_url in self.SEARCH_URLS:
            url = f"{base_url}&page=1" if "?" in base_url else f"{base_url}?page=1"
            logger.info(f"Wellfound PW: fetching {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)

                if page.url.startswith(("https://wellfound.com/auth", "https://auth.wellfound.com")):
                    logger.warning(f"Wellfound: authwall on {url}")
                    continue

                card_selectors = [
                    "a[href*='/company/']",
                    "div[class*='job']",
                    "li[class*='job']",
                    "article[class*='job']",
                    "div[class*='card']",
                    "a[href*='/startup/']",
                    "[class*='job-card']",
                ]

                found = False
                for selector in card_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        found = True
                        break
                    except Exception:
                        continue

                if not found:
                    logger.warning(f"Wellfound PW: no jobs on {url}")
                    continue

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

                html = page.content()
                # Generic /jobs search: no role context, so don't invent a role tag.
                items = self._parse_listing_page(html, "")

                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)

                logger.info(f"Wellfound PW: 1 page -> {len(items)} items")

            except ScrapeBlockedError:
                raise
            except Exception as e:
                logger.warning(f"Wellfound PW error: {e}")

        logger.info(f"Wellfound: {len(all_items)} total lateral items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing_page(self, html: str, role: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        jsonld_scripts = soup.select('script[type="application/ld+json"]')
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string or script.get_text())
                if isinstance(data, dict):
                    data = data.get("@graph") or [data]
                if isinstance(data, list):
                    items = []
                    for entry in data:
                        if isinstance(entry, dict) and entry.get("@type") in ("ItemList", "SearchResultsPage"):
                            for item in entry.get("itemListElement", []):
                                parsed = self._parse_jsonld_item(item, role)
                                if parsed:
                                    items.append(parsed)
                    if items:
                        return self._dedupe_by_link(items)
            except (json.JSONDecodeError, TypeError):
                continue

        cards = soup.select(
            "a[href*='/company/'], div[class*='styles_jobCard'], "
            "li[class*='job-card'], article[class*='job'], div[class*='job-listing'], "
            "div[class*='card'], div[class*='jobCard'], "
            "a[href*='/startup/'], section[class*='job'], "
            "div[class*='listing']"
        )
        if not cards:
            cards = soup.select("[class*='job']:not(script):not(style), [class*='card']:not(script):not(style)")
        items = []
        for card in cards:
            try:
                item = self._parse_card(card, role)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Wellfound card parse error: {exc}")

        return self._dedupe_by_link(items)

    def _parse_jsonld_item(self, item: dict, role: str) -> dict | None:
        if not isinstance(item, dict):
            return None
        # ItemList entries are usually ListItem wrappers: {"@type": "ListItem", "item": {...}}
        job = item["item"] if isinstance(item.get("item"), dict) else item
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
            description = re.sub(r"<[^>]+>", " ", description)
            description = re.sub(r"\s+", " ", description).strip()[:2000]

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

        tags = [role.replace("-", " ").title()] if role else []
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
            "a[href*='/company/'] strong, a[href*='/role/'], "
            "[class*='name'], a[class*='link']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            title = card.get("title", "") or card.get_text(strip=True)[:100]
        if not title:
            return None

        href = ""
        link_tag = card if card.name == "a" else card.select_one("a[href*='/company/'], a[href*='/role/'], a[href*='/startup/'], a[href]")
        if link_tag:
            href = link_tag.get("href", "")
        if not href:
            return None
        link = href if href.startswith("http") else urljoin(self.BASE_URL, href)

        company_el = card.select_one(
            "span[class*='company'], [class*='employer'], [class*='org-name'], "
            "a[class*='company'], div[class*='company'], "
            "[class*='startup'], [class*='org']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "span[class*='location'], span[class*='loc'], div[class*='location'], "
            "[class*='Location'], [class*='loc']"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        # Priority order matters: a bare [class*='comp'] also matches "companyName".
        salary_el = self._select_first(
            card,
            "[class*='compensation'], [class*='salary']",
            "span[class*='pay'], [class*='price'], [class*='amount']",
            "[class*='equity']",
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        tags_els = card.select(
            "span[class*='skill'], span[class*='tag'], [class*='badge'], "
            "span[class*='tech-stack'] span, [class*='tech'], [class*='tool']"
        )
        tags = [s.get_text(strip=True) for s in tags_els if s.get_text(strip=True)]
        if not tags:
            tags = [role.replace("-", " ").title()] if role else []

        desc_el = card.select_one(
            "p[class*='description'], div[class*='desc'], [class*='snippet'], "
            "[class*='summary'], [class*='blurb']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        equity_el = card.select_one("span[class*='equity'], [class*='stock'], [class*='equity']")
        if equity_el and salary:
            salary += f" + {equity_el.get_text(strip=True)}"

        _, exp_min, exp_max = self._infer_experience(title)

        difficulty = self._resolve_experience_level(exp_min, exp_max, title, tags)

        img_el = card.select_one("img[src*='logo'], img[class*='logo'], img[src*='avatar']")
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
