import logging

import httpx

from .base import GenericScraper, infer_deadline_from_posted

logger = logging.getLogger(__name__)


class OnJobScraper(GenericScraper):
    platform_name = "OnJob"
    source_key = "onjob"
    verticals = ["job"]
    BASE_URL = "https://onjob.io"
    FEED_URL = "https://onjob.io/feeds/jobs.json"

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()
        url = self.FEED_URL

        while url:
            logger.info(f"OnJob: fetching {url}")
            try:
                response = client.get(url, timeout=30)
                if not response.is_success:
                    logger.warning(f"OnJob: HTTP {response.status_code} for {url}")
                    break
                data = response.json()
                items_data = data.get("data", [])
                if not items_data:
                    logger.info("OnJob: no data in response, stopping")
                    break
                for raw in items_data:
                    parsed = self._parse_item(raw)
                    if parsed and parsed["link"] not in seen_urls:
                        seen_urls.add(parsed["link"])
                        all_items.append(parsed)
                logger.info(f"OnJob: page -> {len(items_data)} items")
                next_path = data.get("next")
                if next_path:
                    url = f"{self.BASE_URL}{next_path}" if next_path.startswith("/") else next_path
                else:
                    url = None
            except Exception as exc:
                logger.warning(f"OnJob: error fetching {url}: {exc}")
                break

        logger.info(f"OnJob: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_item(self, raw: dict) -> dict | None:
        title = raw.get("title", "")
        if not title:
            return None

        url = raw.get("url", "")
        if not url:
            return None

        company = raw.get("company", {})
        if isinstance(company, dict):
            organizer = company.get("name", "")
        else:
            organizer = str(company) if company else ""

        locations = raw.get("locations", [])
        if isinstance(locations, list):
            location = ", ".join(loc for loc in locations if loc)
        else:
            location = str(locations) if locations else ""

        salary_raw = raw.get("salary_raw", "")

        description = raw.get("description", "")
        if description:
            description = str(description).strip()[:500]

        published_at = raw.get("published_at", "")
        deadline = infer_deadline_from_posted(published_at) if published_at else ""

        employment_type = raw.get("employment_type", "")
        remote = bool(raw.get("remote", False))
        tags = raw.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        return {
            "title": title,
            "type": "job",
            "link": url,
            "organizer": organizer,
            "description": description,
            "location": location,
            "prize": salary_raw,
            "date": deadline,
            "tags": tags,
            "difficulty": self._resolve_experience_level(None, None, title, tags),
            "employment_type": employment_type or None,
            "remote": remote,
            "is_closed": False,
        }
