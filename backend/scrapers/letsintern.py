import logging
import re
from datetime import datetime, timezone, timedelta

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, register_scraper, SourceConfig

logger = logging.getLogger(__name__)


class LetsInternScraper(GenericScraper):
    platform_name = "LetsIntern"
    source_key = "letsintern"
    verticals = ["internship"]
    requires_playwright = True

    BASE_URL = "https://letsintern.in"
    LISTING_URL = f"{BASE_URL}/current-internships/"
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        listings = self._fetch_listings(client)
        logger.info(f"{self.platform_name}: found {len(listings)} listings across {self.MAX_PAGES} pages")

        items = []
        for listing in listings:
            detail = None if listing.get("_skip_detail") else self._fetch_detail(client, listing["link"])
            if detail:
                merged = self._merge(listing, detail)
            else:
                merged = listing
            if merged:
                merged.pop("_skip_detail", None)
                items.append(merged)

        self._log_sample_links(items)
        return items

    def scrape_playwright(self, page) -> list[dict]:
        items = []
        seen_urls: set[str] = set()

        for page_num in range(1, self.MAX_PAGES + 1):
            url = self.LISTING_URL if page_num == 1 else f"{self.LISTING_URL}page/{page_num}/"
            logger.info(f"{self.platform_name} [playwright]: fetching page {page_num}: {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                html = page.content()
                cards = self._parse_listing_page(html)
                for card in cards:
                    if card["link"] not in seen_urls:
                        seen_urls.add(card["link"])
                        items.append(card)
                if not cards:
                    break
            except Exception as exc:
                logger.warning(f"{self.platform_name} [playwright] page {page_num} error: {exc}")
                break

        logger.info(f"{self.platform_name} [playwright]: {len(items)} total items found")
        return items

    def _fetch_listings(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = self.LISTING_URL if page == 1 else f"{self.LISTING_URL}page/{page}/"
            logger.info(f"{self.platform_name}: fetching listing page {page}: {url}")
            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"{self.platform_name} listing page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"{self.platform_name} listing page {page} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        icon_boxes = soup.select(".elementor-widget-icon-box")
        if icon_boxes:
            items = []
            for box in icon_boxes:
                item = self._parse_icon_box(box)
                if item:
                    items.append(item)
            if items:
                return items

        cards = soup.select("div.internship-card, div.internship-item, div[class*='internship'], article, .course-card, .listing-card")
        if not cards:
            cards = soup.select("div.elementor-element div[class*='internship'], div.elementor-column, div[class*='post-']")
        if not cards:
            cards = soup.select("main a[href*='/internship/'], main a[href*='letsintern.in/']")
            if cards:
                return self._parse_flat_links(soup)

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"{self.platform_name}: failed to parse card: {exc}")

        return items

    def _parse_icon_box(self, box) -> dict | None:
        title_el = box.select_one(".elementor-icon-box-title, h3")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title or title.lower() in {"live internships", "current internships"}:
            return None

        desc_el = box.select_one(".elementor-icon-box-description")
        description = desc_el.get_text(" ", strip=True)[:1000] if desc_el else ""
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        tags = self._extract_skills_from_text(f"{title} {description}")
        if "internship" not in [tag.lower() for tag in tags]:
            tags.append("internship")
        deadline = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        return {
            "title": title,
            "type": "internship",
            "link": f"{self.LISTING_URL}#{slug}",
            "organizer": "LetsIntern",
            "description": description,
            "location": "Remote",
            "prize": "",
            "date": deadline,
            "tags": tags,
            "employment_type": "internship",
            "difficulty": self._infer_difficulty(tags),
            "image_url": "",
            "is_closed": False,
            "_skip_detail": True,
        }

    def _parse_flat_links(self, soup: BeautifulSoup) -> list[dict]:
        items: list[dict] = []
        seen: set[str] = set()
        for a in soup.select("a[href*='/internship/']"):
            href = a.get("href", "")
            if not href or href in seen:
                continue
            seen.add(href)
            link = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            title = a.get_text(strip=True) or self._title_from_url(link)
            parent = a.find_parent(["div", "section", "article"])
            description = ""
            if parent:
                p = parent.select_one("p")
                if p:
                    description = p.get_text(strip=True)[:500]
            items.append({
                "title": title,
                "type": "internship",
                "link": link,
                "organizer": "LetsIntern",
                "description": description,
                "location": "Remote",
                "prize": "",
                "date": "",
                "tags": ["internship"],
                "employment_type": "internship",
                "difficulty": "beginner",
                "image_url": "",
                "is_closed": False,
            })
        return items

    def _parse_card(self, card) -> dict | None:
        title_el = card.select_one("h2, h3, h4, h5, .title, .internship-title, .course-title")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            a_title = card.select_one("a[href*='/internship/'], a[href*='letsintern.in/']")
            if a_title:
                title = a_title.get_text(strip=True)
        if not title:
            return None

        link_el = card.select_one("a[href*='/internship/'], a[href*='letsintern.in/']")
        href = ""
        if link_el:
            href = link_el.get("href", "")
        if not href:
            a_all = card.select_one("a[href]")
            if a_all:
                href = a_all.get("href", "")
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        desc_el = card.select_one("p, .description, .internship-description, .course-description")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        image_url = ""
        img_el = card.select_one("img")
        if img_el:
            src = img_el.get("src", "") or img_el.get("data-src", "")
            if src:
                image_url = src if src.startswith("http") else f"{self.BASE_URL}{src}"

        deadline = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": "LetsIntern",
            "description": description,
            "location": "Remote",
            "prize": "",
            "date": deadline,
            "tags": ["internship"],
            "employment_type": "internship",
            "difficulty": "beginner",
            "image_url": image_url,
            "is_closed": False,
        }

    def _fetch_detail(self, client: httpx.Client, url: str) -> dict | None:
        try:
            response = client.get(url, timeout=30)
            if not response.is_success:
                logger.debug(f"{self.platform_name} detail {url}: HTTP {response.status_code}")
                return None
            return self._parse_detail_page(response.text)
        except Exception as exc:
            logger.debug(f"{self.platform_name} detail {url} error: {exc}")
            return None

    def _parse_detail_page(self, html_text: str) -> dict | None:
        soup = BeautifulSoup(html_text, "html.parser")
        result: dict = {}

        title_el = soup.select_one("h1, .entry-title, .internship-title, h2")
        if title_el:
            result["title"] = title_el.get_text(strip=True)

        desc_sections = soup.select("div.elementor-widget-text-editor p, .entry-content p, .internship-content p, main p")
        desc_parts = [p.get_text(strip=True) for p in desc_sections if len(p.get_text(strip=True)) > 30]
        if desc_parts:
            result["description"] = " ".join(desc_parts)[:2000]
        else:
            for tag in soup.select("p, li, span"):
                text = tag.get_text(strip=True)
                if len(text) > 60:
                    desc_parts.append(text)
            if desc_parts:
                result["description"] = " ".join(desc_parts)[:2000]

        page_text = soup.get_text()
        stipend_match = re.search(
            r"(?:stipend|salary|pay)(?:\s*[:-])?\s*(?:.*?)?(?:₹|Rs\.?\s*)?([\d,]+(?:\s*[-–]\s*[\d,]+)?)(?:\s*(?:per\s*)?month|/month)?",
            page_text, re.IGNORECASE
        )
        if stipend_match:
            result["prize"] = f"Rs. {stipend_match.group(1)}"

        stipend_simple = re.search(r"(?:₹|Rs\.?\s*)([\d,]+(?:\s*[-–]\s*[\d,]+)?)", page_text)
        if stipend_simple and "prize" not in result:
            result["prize"] = f"Rs. {stipend_simple.group(1)}"

        duration_match = re.search(r"(\d+)\s*(?:month|Month)", page_text)
        if duration_match:
            result["duration"] = f"{duration_match.group(1)} Months"

        skills = []
        skill_keywords = ["Python", "JavaScript", "HTML", "CSS", "React", "Node", "SQL",
                         "Machine Learning", "Data Science", "AI", "Web Development",
                         "Django", "Flask", "Java", "C++", "API", "Git", "Docker"]
        skills = self._extract_skills_from_text(page_text)
        if skills:
            result["tags"] = skills

        return result

    def _extract_skills_from_text(self, text: str) -> list[str]:
        skills = []
        skill_keywords = ["Python", "JavaScript", "HTML", "CSS", "React", "Node", "SQL",
                         "Machine Learning", "Data Science", "AI", "Web Development",
                         "Django", "Flask", "Java", "C++", "API", "Git", "Docker",
                         "DevOps", "Power BI", "Tableau", "Embedded", "IoT", "Cybersecurity"]
        for skill in skill_keywords:
            if re.search(re.escape(skill), text, re.IGNORECASE):
                skills.append(skill)
        return skills

    def _title_from_url(self, url: str) -> str:
        path = url.rstrip("/").split("/")[-1]
        name = path.replace("-", " ").replace("_", " ").title()
        return f"{name} Intern"

    def _merge(self, listing: dict, detail: dict) -> dict:
        merged = {**listing}
        for key, value in detail.items():
            if value and (not merged.get(key) or key in ("description", "prize", "tags")):
                merged[key] = value
        if detail.get("tags"):
            merged["difficulty"] = self._infer_difficulty(detail["tags"])
        return merged

