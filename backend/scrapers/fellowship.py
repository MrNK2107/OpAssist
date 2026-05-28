import logging
import re
import json
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class FellowshipScraper(GenericScraper):
    """Fellowship scraper — tech fellowships and open source programs.

    Scrapes program pages for:
    - C4GT (Code for GovTech) — open source government tech projects
    - Outreachy — paid internships in open source
    - MLH Fellowship — software engineering fellowships
    """

    platform_name = "Fellowship"

    PROGRAMS = [
        {
            "url": "https://codeforgovtech.in/",
            "name": "Code for GovTech (C4GT)",
            "organizer": "Code for GovTech",
            "description": "Contribute to open source government technology projects. Get mentored, build your portfolio, and make an impact on public services in India.",
            "tags": ["fellowship", "open-source", "govtech"],
        },
        {
            "url": "https://www.outreachy.org/",
            "name": "Outreachy Internships",
            "organizer": "Outreachy",
            "description": "Paid, remote internships in open source for people underrepresented in tech. Work on real projects with mentorship from experienced developers.",
            "tags": ["fellowship", "open-source", "internship"],
        },
        {
            "url": "https://fellowship.mlh.io/",
            "name": "MLH Fellowship",
            "organizer": "Major League Hacking",
            "description": "A 12-week remote internship alternative. Build real software, learn from industry mentors, and join the MLH community.",
            "tags": ["fellowship", "hackathon", "software-engineering"],
        },
    ]

    def scrape(self, client: httpx.Client) -> list[dict]:
        items: list[dict] = []

        for program in self.PROGRAMS:
            item = self._scrape_program(client, program)
            if item:
                items.append(item)

        logger.info(f"Fellowship: {len(items)} programs found")
        return items

    def _scrape_program(self, client: httpx.Client, program: dict) -> dict | None:
        """Scrape a single fellowship program page."""
        url = program["url"]
        logger.info(f"Fellowship: fetching {program['name']}: {url}")

        try:
            response = client.get(url, timeout=30)
            if not response.is_success:
                logger.warning(f"Fellowship {program['name']}: HTTP {response.status_code}")
                return self._build_item(program, "", "")

            soup = BeautifulSoup(response.text, "html.parser")

            deadline = self._extract_deadline(soup)
            description = self._extract_description(soup, program["description"])
            image_url = self._extract_image(soup)

            return self._build_item(program, deadline, description, image_url)

        except Exception as exc:
            logger.warning(f"Fellowship {program['name']} error: {exc}")
            return self._build_item(program, "", "")

    def _extract_deadline(self, soup: BeautifulSoup) -> str:
        """Try to find application deadlines on the page."""
        text = soup.get_text()

        patterns = [
            r"(?:deadline|apply\s+by|applications?\s+close|last\s+date)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
            r"(?:deadline|apply\s+by|applications?\s+close)\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(?:deadline|apply\s+by)\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                for fmt in ["%B %d, %Y", "%B %d %Y", "%b %d, %Y",
                            "%d %B %Y", "%d %b %Y", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                        if dt > datetime.now(timezone.utc):
                            return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or script.get_text())
                if isinstance(data, dict):
                    end_date = data.get("endDate", "")
                    if end_date:
                        dt = datetime.strptime(end_date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        if dt > datetime.now(timezone.utc):
                            return dt.strftime("%Y-%m-%d")
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        return ""

    def _extract_description(self, soup: BeautifulSoup, fallback: str) -> str:
        """Extract description from the page."""
        meta = soup.select_one('meta[name="description"], meta[property="og:description"]')
        if meta:
            content = meta.get("content", "").strip()
            if content and len(content) > 50:
                return content[:2000]

        for p in soup.select("p"):
            text = p.get_text(strip=True)
            if len(text) > 80 and "cookie" not in text.lower():
                return text[:2000]

        return fallback

    def _extract_image(self, soup: BeautifulSoup) -> str:
        """Try to extract an og:image or logo."""
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image:
            src = og_image.get("content", "")
            if src:
                return src
        return ""

    def _build_item(self, program: dict, deadline: str, description: str, image_url: str = "") -> dict:
        return {
            "title": program["name"],
            "type": "event",
            "link": program["url"],
            "organizer": program["organizer"],
            "description": description or program["description"],
            "location": "Remote",
            "prize": "",
            "date": deadline,
            "tags": program["tags"],
            "difficulty": "intermediate",
            "image_url": image_url,
            "is_closed": False,
        }
