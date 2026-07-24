import logging
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class HackerEarthScraper(GenericScraper):
    """HackerEarth scraper — challenges, hackathons, hiring."""

    platform_name = "HackerEarth"
    source_key = "hackerearth"
    verticals = ["hackathon", "internship"]
    COMPETE_URL = "https://www.hackerearth.com/api/community/challenges/compete/"
    HIRING_URL = "https://www.hackerearth.com/api/community/challenges/hiring/"

    def scrape(self, client: httpx.Client) -> list[dict]:
        items: list[dict] = []

        logger.info(f"HackerEarth stage: fetching compete challenges")
        items.extend(self._fetch_endpoint(client, self.COMPETE_URL))

        logger.info(f"HackerEarth stage: fetching hiring challenges")
        items.extend(self._fetch_endpoint(client, self.HIRING_URL))

        logger.info(f"HackerEarth stage: total items={len(items)}")
        self._log_sample_links(items)
        return items

    def _fetch_endpoint(self, client: httpx.Client, url: str) -> list[dict]:
        try:
            response = client.get(url)
            if not response.is_success:
                logger.warning(f"HackerEarth API request failed with status {response.status_code} for {url}")
                return []
            payload = response.json()
            data = payload.get("data", [])
            return self._parse_items(data)
        except Exception as exc:
            logger.warning(f"HackerEarth API fetch failed for {url}: {exc}")
            return []

    def _parse_items(self, data: list[dict]) -> list[dict]:
        items = []
        now = datetime.now(timezone.utc)

        for event in data:
            end_str = event.get("end")
            deadline = self._parse_iso_date(end_str)

            # Skip events with past deadlines
            if deadline:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if deadline_dt < now:
                    continue

            title = (event.get("title") or "").strip()
            if not title:
                continue

            event_url = event.get("url", "")
            link = event_url if event_url.startswith("http") else f"https://www.hackerearth.com{event_url}" if event_url else ""

            event_type = event.get("type", "")

            # Determine opportunity type from challenge_type / sub_type / event_type
            challenge_type = event.get("challenge_type") or event.get("sub_type") or ""
            if challenge_type:
                ct = challenge_type.lower()
                if ct == "internship" or "intern" in ct:
                    opp_type = "internship"
                elif ct == "full time" or ct == "fulltime" or "full" in ct:
                    opp_type = "job"
                else:
                    opp_type = "internship"
            elif event_type == "Hackathon":
                opp_type = "hackathon"
            else:
                opp_type = "internship"

            company = event.get("company_name", "")
            organizer = company if company else "HackerEarth"

            image_url = (
                event.get("cover_image")
                or event.get("listing_image")
                or event.get("image_url")
                or ""
            )

            # Description
            description = event.get("description") or ""
            if not description:
                label = challenge_type or event_type or "challenge"
                description = f"{title} is a HackerEarth {label} hosted by {organizer}."

            # Prize / reward / salary
            prize = event.get("prize") or event.get("reward") or event.get("salary") or ""

            # Tags from skills or technologies arrays + event_type tag
            tags = []
            if event_type:
                tags.append(event_type.lower())
            for skill_list_key in ("skills", "technologies"):
                raw_skills = event.get(skill_list_key, [])
                if isinstance(raw_skills, list):
                    for s in raw_skills:
                        if isinstance(s, str) and s:
                            tags.append(s.lower())
                elif isinstance(raw_skills, str) and raw_skills:
                    tags.append(raw_skills.lower())

            # Location
            city = event.get("city") or event.get("location") or ""
            is_remote = event.get("is_remote", False)
            if isinstance(is_remote, str):
                is_remote = is_remote.lower() in ("true", "1", "yes")
            if is_remote:
                location = "Remote"
                if city:
                    location = f"Remote — {city}"
            elif city:
                location = city
            else:
                location = "Online"

            items.append({
                "title": title,
                "organizer": organizer,
                "start_date": self._parse_iso_date(event.get("start")),
                "end_date": deadline,
                "date": deadline or "",
                "location": location,
                "link": link,
                "source_platform": "HackerEarth",
                "description": description,
                "prize": prize,
                "tags": tags,
                "difficulty": self._infer_difficulty(tags),
                "type": opp_type,
                "is_closed": False,
                "image_url": image_url,
            })

        return items

    @staticmethod
    def _parse_iso_date(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None
