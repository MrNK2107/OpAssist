import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class InternshalaScraper(GenericScraper):
    """Internshala scraper — internships from internshala.com.

    Two-pass approach:
    1. Parse listing pages to discover URLs and extract basic fields
    2. Fetch detail pages for full JSON-LD JobPosting data
    """

    platform_name = "Internshala"
    BASE_URL = "https://internshala.com"
    LISTING_URL = f"{BASE_URL}/internships"
    MAX_PAGES = 3  # ~150 internships per run

    def scrape(self, client: httpx.Client) -> list[dict]:
        # Pass 1: collect detail URLs and basic data from listing pages
        listings = self._fetch_listings(client)
        logger.info(f"Internshala: found {len(listings)} listings across {self.MAX_PAGES} pages")

        if not listings:
            return []

        # Pass 2: enrich with detail page data
        items = []
        for listing in listings:
            detail = self._fetch_detail(client, listing["link"])
            if detail:
                merged = self._merge(listing, detail)
            else:
                merged = listing
            if merged:
                items.append(merged)

        logger.info(f"Internshala: {len(items)} items after enrichment")
        return items

    def _fetch_listings(self, client: httpx.Client) -> list[dict]:
        """Parse listing pages to get basic data and detail URLs."""
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for page in range(1, self.MAX_PAGES + 1):
            url = f"{self.LISTING_URL}/page-{page}/" if page > 1 else f"{self.LISTING_URL}/"
            logger.info(f"Internshala: fetching listing page {page}: {url}")

            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"Internshala listing page {page}: HTTP {response.status_code}")
                    break
                items = self._parse_listing_page(response.text)
                for item in items:
                    if item["link"] not in seen_urls:
                        seen_urls.add(item["link"])
                        all_items.append(item)
                if not items:
                    break
            except Exception as exc:
                logger.warning(f"Internshala listing page {page} error: {exc}")
                break

        return all_items

    def _parse_listing_page(self, html_text: str) -> list[dict]:
        """Extract internship data from a listing page's HTML."""
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.individual_internship")
        items: list[dict] = []

        for card in cards:
            try:
                item = self._parse_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Internshala: failed to parse card: {exc}")

        return items

    def _parse_card(self, card) -> dict | None:
        """Parse a single internship card from the listing page."""
        # Title
        title_el = card.select_one("h2.job-internship-name a.job-title-href")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        # Link to detail page (from data-href attribute or anchor)
        href = card.get("data-href", "")
        if not href:
            link_el = card.select_one('a[href*="/internship/detail/"]')
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        # Company (p.company-name avoids "Actively hiring" badge)
        company_el = card.select_one("p.company-name")
        company = company_el.get_text(strip=True) if company_el else ""

        # Location — inside .row-1-item.locations
        location_el = card.select_one(".row-1-item.locations span a")
        location = location_el.get_text(strip=True) if location_el else ""

        # Stipend
        stipend_el = card.select_one("span.stipend")
        stipend = stipend_el.get_text(strip=True) if stipend_el else ""

        # Duration — .detail-row-1 .row-1-item with ic-16-calendar icon
        duration = ""
        for item in card.select(".detail-row-1 .row-1-item"):
            icon = item.select_one("i")
            if icon and "ic-16-calendar" in " ".join(icon.get("class", [])):
                duration = item.get_text(strip=True)
                break

        # Skills / tags — .job_skill elements
        tags = [s.get_text(strip=True) for s in card.select("div.job_skill") if s.get_text(strip=True)]

        # Description — .about_job .text
        desc_el = card.select_one(".about_job .text")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        # Posted date (e.g., "2 weeks ago", "Today") — for deadline inference
        posted_text = ""
        posted_el = card.select_one(".status-inactive span, .status_s span")
        if posted_el:
            posted_text = posted_el.get_text(strip=True)

        # No deadline on listing pages — infer from posted date
        deadline = self._infer_deadline_from_posted(posted_text)

        # Company logo (skip placeholder logos)
        logo_el = card.select_one(".internship_logo img")
        image_url = ""
        if logo_el:
            src = logo_el.get("src", "")
            if src and "placeholder" not in src:
                image_url = src if src.startswith("http") else f"{self.BASE_URL}{src}"

        return {
            "title": title,
            "type": "internship",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": stipend,
            "date": deadline if deadline else "",
            "tags": tags,
            "difficulty": self._infer_difficulty(tags),
            "image_url": image_url,
            "is_closed": False,
        }

    def _fetch_detail(self, client: httpx.Client, url: str) -> dict | None:
        """Fetch a detail page and extract JSON-LD JobPosting data."""
        try:
            response = client.get(url, timeout=30)
            if not response.is_success:
                logger.debug(f"Internshala detail {url}: HTTP {response.status_code}")
                return None
            return self._parse_detail_page(response.text)
        except Exception as exc:
            logger.debug(f"Internshala detail {url} error: {exc}")
            return None

    def _parse_detail_page(self, html_text: str) -> dict | None:
        """Extract JobPosting JSON-LD from a detail page."""
        soup = BeautifulSoup(html_text, "html.parser")
        scripts = soup.select('script[type="application/ld+json"]')

        for script in scripts:
            try:
                import json
                data = json.loads(script.string or script.get_text())
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    return self._extract_from_jobposting(data)
            except (json.JSONDecodeError, TypeError):
                continue

        return None

    def _extract_from_jobposting(self, jp: dict) -> dict:
        """Extract fields from a JSON-LD JobPosting object."""
        result: dict = {}

        # Title
        if jp.get("title"):
            result["title"] = jp["title"]

        # Description (HTML -> plain text)
        desc = jp.get("description", "")
        if desc:
            desc = re.sub(r"<[^>]+>", " ", desc)
            desc = re.sub(r"\s+", " ", desc).strip()[:2000]
            result["description"] = desc

        # Organization
        org = jp.get("hiringOrganization", {})
        if isinstance(org, dict) and org.get("name"):
            result["organizer"] = org["name"]

        # Location — Internshala uses a single Place object, not a list
        loc_data = jp.get("jobLocation", {})
        if isinstance(loc_data, list) and loc_data:
            loc_data = loc_data[0]
        if isinstance(loc_data, dict):
            addr = loc_data.get("address", {})
            parts = [
                addr.get("addressLocality", ""),
                addr.get("addressRegion", ""),
            ]
            loc = ", ".join(p for p in parts if p)
            if loc:
                result["location"] = loc

        # Salary / stipend
        salary = jp.get("baseSalary", {})
        if salary:
            result["prize"] = self._format_salary(salary)

        # Deadline
        valid_through = jp.get("validThrough", "")
        if valid_through:
            deadline = self._parse_deadline(valid_through)
            if deadline:
                result["date"] = deadline.strftime("%Y-%m-%d")

        # Date posted
        date_posted = jp.get("datePosted", "")
        if date_posted:
            try:
                dp = datetime.strptime(date_posted, "%Y-%m-%d")
                result["start_date"] = dp.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Skills
        skills = jp.get("skills", "")
        if skills and isinstance(skills, str):
            result["tags"] = [s.strip() for s in skills.split(",") if s.strip()]

        # Number of openings
        openings = jp.get("totalJobOpenings")
        if openings:
            result["openings"] = openings

        return result

    def _format_salary(self, salary: dict) -> str:
        """Format a JSON-LD baseSalary into a readable string."""
        value = salary.get("value", {})
        currency = salary.get("currency", "INR")
        symbol = "₹" if currency == "INR" else f"{currency} "

        if isinstance(value, dict):
            min_val = value.get("minValue")
            max_val = value.get("maxValue")
            unit = value.get("unitText", "MONTH")
            unit_str = "/month" if unit == "MONTH" else "/year" if unit == "YEAR" else ""

            if min_val and max_val:
                return f"{symbol}{min_val:,} - {max_val:,} {unit_str}"
            elif min_val:
                return f"{symbol}{min_val:,} {unit_str}"
            elif max_val:
                return f"{symbol}{max_val:,} {unit_str}"
        elif isinstance(value, (int, float)):
            return f"{symbol}{value:,.0f}"

        return ""

    def _parse_deadline(self, raw: str) -> datetime | None:
        """Parse deadline string to timezone-aware UTC datetime."""
        if not raw:
            return None
        # Try common formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d %b %Y", "%b %d, %Y"]:
            try:
                return datetime.strptime(raw.strip(), fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        # Try ISO format
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass
        # Try "14 Jun' 26" format (Internshala specific)
        m = re.match(r"(\d{1,2})\s+(\w+)'?\s*(\d{2,4})", raw.strip())
        if m:
            day, month_str, year = m.groups()
            if len(year) == 2:
                year = "20" + year
            try:
                return datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    return datetime.strptime(f"{day} {month_str} {year}", "%d %B %Y").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        return None

    def _infer_deadline_from_posted(self, posted_text: str) -> str:
        """Infer approximate deadline from 'posted X days/weeks ago' text.
        Internshala internships typically have ~30 day listing windows."""
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month)", posted_text, re.IGNORECASE)
        if not match:
            if "today" in posted_text.lower() or "just now" in posted_text.lower():
                # Posted today: deadline ~30 days out
                deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(days=30)
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
        deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")

    def _merge(self, listing: dict, detail: dict) -> dict:
        """Merge listing data with detail page data. Detail takes priority."""
        merged = {**listing}
        for key, value in detail.items():
            if value and (not merged.get(key) or key in ("description", "date", "prize", "tags")):
                merged[key] = value
        # Recalculate difficulty if tags were enriched
        if detail.get("tags"):
            merged["difficulty"] = self._infer_difficulty(detail["tags"])
        return merged
