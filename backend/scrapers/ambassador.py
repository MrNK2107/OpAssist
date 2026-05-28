import logging
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper

logger = logging.getLogger(__name__)


class AmbassadorScraper(GenericScraper):
    """Ambassador program scraper — campus ambassador and student programs.

    Scrapes known program pages for major tech companies:
    - Google Developer Student Clubs (GDSC)
    - Microsoft Learn Student Ambassadors (MLSA)
    - GitHub Campus Expert
    - AWS Cloud Club Captain
    """

    platform_name = "Ambassador"

    # Known ambassador program URLs (stable, long-lived)
    PROGRAMS = [
        {
            "url": "https://developers.google.com/community/gdsc",
            "name": "Google Developer Student Clubs",
            "organizer": "Google",
            "description": "Lead a GDSC chapter at your university. Build your developer portfolio, learn Google technologies, and impact your campus community.",
        },
        {
            "url": "https://studentambassadors.microsoft.com/",
            "name": "Microsoft Learn Student Ambassadors",
            "organizer": "Microsoft",
            "description": "Join a global community of student leaders. Learn Microsoft technologies, earn certifications, and mentor peers.",
        },
        {
            "url": "https://education.github.com/experts",
            "name": "GitHub Campus Expert",
            "organizer": "GitHub",
            "description": "Become a GitHub Campus Expert. Build technical communities on campus, organize events, and develop leadership skills.",
        },
        {
            "url": "https://aws.amazon.com/developer/community/community-groups/",
            "name": "AWS Cloud Club Captain",
            "organizer": "Amazon Web Services",
            "description": "Lead an AWS Cloud Club at your university. Learn cloud technologies and build a community of cloud enthusiasts.",
        },
    ]

    def scrape(self, client: httpx.Client) -> list[dict]:
        items: list[dict] = []

        for program in self.PROGRAMS:
            item = self._scrape_program(client, program)
            if item:
                items.append(item)

        logger.info(f"Ambassador: {len(items)} programs found")
        return items

    def _scrape_program(self, client: httpx.Client, program: dict) -> dict | None:
        """Scrape a single ambassador program page for details."""
        url = program["url"]
        logger.info(f"Ambassador: fetching {program['name']}: {url}")

        try:
            response = client.get(url, timeout=30)
            if not response.is_success:
                logger.warning(f"Ambassador {program['name']}: HTTP {response.status_code}")
                # Return with static data even if page fails
                return self._build_item(program, "")

            soup = BeautifulSoup(response.text, "html.parser")

            # Try to extract application status / deadline
            deadline = self._extract_deadline(soup)
            description = self._extract_description(soup, program["description"])

            return self._build_item(program, deadline, description)

        except Exception as exc:
            logger.warning(f"Ambassador {program['name']} error: {exc}")
            # Return with static data even on error
            return self._build_item(program, "")

    def _extract_deadline(self, soup: BeautifulSoup) -> str:
        """Try to find a deadline or application date on the page."""
        # Look for common deadline patterns
        deadline_patterns = [
            r"(?:deadline|apply\s+by|last\s+date|closes?)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})",
            r"(?:deadline|apply\s+by|last\s+date)\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})",
            r"(\w+\s+\d{1,2},?\s+20\d{2})",
        ]

        text = soup.get_text()
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                for fmt in ["%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                        if dt > datetime.now(timezone.utc):
                            return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

        return ""

    def _extract_description(self, soup: BeautifulSoup, fallback: str) -> str:
        """Try to extract a description from the page."""
        # Try meta description
        meta = soup.select_one('meta[name="description"]')
        if meta:
            content = meta.get("content", "").strip()
            if content and len(content) > 50:
                return content[:1000]

        # Try first meaningful paragraph
        for p in soup.select("p"):
            text = p.get_text(strip=True)
            if len(text) > 100 and "cookie" not in text.lower():
                return text[:1000]

        return fallback

    def _build_item(self, program: dict, deadline: str, description: str = "") -> dict:
        return {
            "title": program["name"],
            "type": "ambassador",
            "link": program["url"],
            "organizer": program["organizer"],
            "description": description or program["description"],
            "location": "Remote / Campus",
            "prize": "",
            "date": deadline,
            "tags": ["ambassador", "campus", program["organizer"].lower()],
            "difficulty": "intermediate",
            "image_url": "",
            "is_closed": False,
        }
