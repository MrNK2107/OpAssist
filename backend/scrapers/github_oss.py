import logging
import httpx
from .base import GenericScraper

logger = logging.getLogger(__name__)


class GitHubOSSScraper(GenericScraper):
    """GitHub OSS scraper — GSoC orgs, Hacktoberfest repos."""

    platform_name = "GitHub"
    GSOC_ORGS_URL = "https://api.github.com/search/repositories?q=topic:gsoc+topic:summer-of-code&sort=stars&per_page=30"
    HACKTOBERFEST_URL = "https://api.github.com/search/repositories?q=topic:hacktoberfest+stars:>100&sort=stars&per_page=30"

    def scrape(self, client: httpx.Client) -> list[dict]:
        items: list[dict] = []

        logger.info("GitHub OSS stage: fetching GSoC orgs")
        items.extend(self._fetch_repos(client, self.GSOC_ORGS_URL, "gsoc"))

        logger.info("GitHub OSS stage: fetching Hacktoberfest repos")
        items.extend(self._fetch_repos(client, self.HACKTOBERFEST_URL, "hacktoberfest"))

        logger.info(f"GitHub OSS stage: items={len(items)}")
        return items

    def _fetch_repos(self, client: httpx.Client, url: str, source_tag: str) -> list[dict]:
        try:
            response = client.get(url)
            if not response.is_success:
                logger.warning(f"GitHub API failed with status {response.status_code}")
                return []
            payload = response.json()
            return self._parse_repos(payload.get("items", []), source_tag)
        except Exception as exc:
            logger.warning(f"GitHub fetch failed: {exc}")
            return []

    def _parse_repos(self, repos: list, source_tag: str) -> list[dict]:
        items = []
        for repo in repos:
            if not isinstance(repo, dict):
                continue
            name = repo.get("full_name") or repo.get("name") or ""
            if not name:
                continue
            owner = repo.get("owner", {})
            items.append({
                "title": name,
                "organizer": owner.get("login", ""),
                "link": repo.get("html_url") or "",
                "source_platform": "GitHub",
                "description": repo.get("description") or "",
                "tags": repo.get("topics", []),
                "type": "oss",
                "is_closed": repo.get("archived", False),
                "prize": f"Stars: {repo.get('stargazers_count', 0)}",
                "image_url": owner.get("avatar_url") or "",
                "location": "Remote",
                "date": "",
                "difficulty": "intermediate",
                "start_date": None,
                "end_date": None,
            })
        return items
