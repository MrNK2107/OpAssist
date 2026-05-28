import logging
import re
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class GitHubOSSScraper(GenericScraper):
    """GitHub OSS scraper — real open source projects seeking contributors.

    Finds projects through actual contributor-friendly signals:
    1. Issues labeled 'good first issue' — beginner-friendly tasks
    2. Issues labeled 'help wanted' — maintainer-validated tasks
    3. GSoC organizations — Google Summer of Code participating orgs

    Instead of just scraping top-starred repos, this finds projects that
    are actively welcoming contributions right now.
    """

    platform_name = "GitHub"
    API_BASE = "https://api.github.com"
    MAX_RESULTS_PER_QUERY = 100
    HEADERS = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Searches that find contributor-friendly projects
    ISSUE_SEARCHES = [
        # Good first issues in popular languages for Indian students
        "label:\"good first issue\" language:python state:open",
        "label:\"good first issue\" language:javascript state:open",
        "label:\"good first issue\" language:typescript state:open",
        "label:\"good first issue\" language:java state:open",
        "label:\"good first issue\" language:rust state:open",
        "label:\"good first issue\" language:go state:open",
        # Help wanted issues
        "label:\"help wanted\" language:python state:open",
        "label:\"help wanted\" language:javascript state:open",
    ]

    # Curated list of active, contributor-friendly organizations
    CURATED_ORGS = [
        "facebook", "microsoft", "google", "apache", "mozilla",
        "rust-lang", "nodejs", "django", "flask", "fastapi",
        "vercel", "supabase", "langchain-ai", "huggingface",
        "pytorch", "tensorflow", "scikit-learn", "pandas-dev",
        "matplotlib", "astral-sh", "encode", "psf",
        "bitcoin", "ethereum", "solana-labs",
    ]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_repos: dict[str, dict] = {}  # keyed by full_name to deduplicate

        # Method 1: Find repos through good-first-issue / help-wanted issues
        issue_repos = self._scrape_from_issues(client)
        for repo in issue_repos:
            key = repo.get("full_name", "")
            if key and key not in all_repos:
                all_repos[key] = repo

        # Method 2: Scrape curated orgs for active repos
        org_repos = self._scrape_curated_orgs(client)
        for repo in org_repos:
            key = repo.get("full_name", "")
            if key and key not in all_repos:
                all_repos[key] = repo

        # Method 3: GSoC organizations (seasonal, but valuable)
        gsoc_repos = self._scrape_gsoc_orgs(client)
        for repo in gsoc_repos:
            key = repo.get("full_name", "")
            if key and key not in all_repos:
                all_repos[key] = repo

        items = list(all_repos.values())
        logger.info(f"GitHubOSS: {len(items)} total unique repos")
        return items

    def _scrape_from_issues(self, client: httpx.Client) -> list[dict]:
        """Find contributor-friendly repos by searching for labeled issues."""
        repos: list[dict] = []
        seen_repos: set[str] = set()

        for query in self.ISSUE_SEARCHES:
            try:
                results = self._search_issues(client, query)
                for item in results:
                    repo_info = item.get("repository", {})
                    full_name = repo_info.get("full_name", "")
                    if not full_name or full_name in seen_repos:
                        continue
                    seen_repos.add(full_name)

                    repo = self._build_repo_from_issue(item, repo_info)
                    if repo:
                        repos.append(repo)
            except Exception as exc:
                logger.warning(f"GitHubOSS issue search failed for '{query}': {exc}")

        logger.info(f"GitHubOSS: {len(repos)} repos from issue search")
        return repos

    def _search_issues(self, client: httpx.Client, query: str) -> list[dict]:
        """Search GitHub issues API."""
        url = f"{self.API_BASE}/search/issues"
        params = {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": min(self.MAX_RESULTS_PER_QUERY, 30),  # API limit
        }

        response = client.get(url, params=params, headers=self.HEADERS, timeout=30)

        if response.status_code == 403:
            logger.warning("GitHubOSS: rate limited on issue search")
            return []
        if response.status_code == 422:
            logger.warning(f"GitHubOSS: invalid query: {query}")
            return []
        if not response.is_success:
            logger.warning(f"GitHubOSS issue search: HTTP {response.status_code}")
            return []

        data = response.json()
        return data.get("items", [])

    def _build_repo_from_issue(self, issue: dict, repo_info: dict) -> dict | None:
        """Build an opportunity from a repo discovered via issue search."""
        full_name = repo_info.get("full_name", "")
        if not full_name:
            return None

        repo_url = repo_info.get("html_url", f"https://github.com/{full_name}")
        description = repo_info.get("description", "") or ""
        stars = repo_info.get("stargazers_count", 0)
        language = repo_info.get("language", "") or ""
        topics = repo_info.get("topics", []) or []

        # Get issue context for richer description
        issue_title = issue.get("title", "")
        issue_labels = [l.get("name", "") for l in issue.get("labels", [])]

        # Determine if this is good-first-issue or help-wanted
        is_good_first = any("good first" in l.lower() for l in issue_labels)
        is_help_wanted = any("help wanted" in l.lower() for l in issue_labels)

        tag_list = topics[:5] if topics else []
        if language:
            tag_list.append(language.lower())
        if is_good_first:
            tag_list.append("good first issue")
        if is_help_wanted:
            tag_list.append("help wanted")

        # Enrich description with issue context
        enriched_desc = description
        if issue_title:
            enriched_desc += f" Example task: {issue_title}"

        return {
            "title": f"Contribute to {full_name}",
            "type": "oss",
            "link": repo_url,
            "organizer": full_name.split("/")[0],
            "description": enriched_desc[:1000],
            "location": "Remote",
            "prize": f"★ {stars:,}" if stars else "",
            "date": "",
            "tags": tag_list,
            "difficulty": "beginner" if is_good_first else "intermediate",
            "image_url": repo_info.get("owner", {}).get("avatar_url", ""),
            "is_closed": False,
        }

    def _scrape_curated_orgs(self, client: httpx.Client) -> list[dict]:
        """Find active repos from curated organizations."""
        repos: list[dict] = []

        for org in self.CURATED_ORGS[:10]:  # Limit to avoid rate limits
            try:
                org_repos = self._fetch_org_repos(client, org)
                repos.extend(org_repos)
            except Exception as exc:
                logger.debug(f"GitHubOSS: failed to fetch org {org}: {exc}")

        logger.info(f"GitHubOSS: {len(repos)} repos from curated orgs")
        return repos

    def _fetch_org_repos(self, client: httpx.Client, org: str) -> list[dict]:
        """Fetch recent active repos from an organization."""
        url = f"{self.API_BASE}/orgs/{org}/repos"
        params = {
            "sort": "updated",
            "direction": "desc",
            "per_page": 10,
        }

        response = client.get(url, params=params, headers=self.HEADERS, timeout=30)
        if not response.is_success:
            return []

        repos_data = response.json()
        repos: list[dict] = []

        for repo in repos_data:
            if repo.get("archived") or repo.get("fork"):
                continue
            # Only include repos with decent activity
            stars = repo.get("stargazers_count", 0)
            if stars < 50:
                continue

            # Check if repo has good-first-issue or help-wanted labels
            has_contributor_labels = self._check_contributor_labels(client, repo.get("full_name", ""))

            topics = repo.get("topics", []) or []
            language = repo.get("language", "") or ""
            tag_list = topics[:5]
            if language:
                tag_list.append(language.lower())
            if has_contributor_labels:
                tag_list.append("good first issue")

            repos.append({
                "title": f"Contribute to {repo['full_name']}",
                "type": "oss",
                "link": repo.get("html_url", ""),
                "organizer": org,
                "description": (repo.get("description", "") or "")[:1000],
                "location": "Remote",
                "prize": f"★ {stars:,}",
                "date": "",
                "tags": tag_list,
                "difficulty": "beginner" if has_contributor_labels else "intermediate",
                "image_url": repo.get("owner", {}).get("avatar_url", ""),
                "is_closed": False,
            })

        return repos

    def _check_contributor_labels(self, client: httpx.Client, full_name: str) -> bool:
        """Check if a repo has good-first-issue or help-wanted labels."""
        if not full_name:
            return False
        try:
            url = f"{self.API_BASE}/repos/{full_name}/labels"
            params = {"per_page": 100}
            response = client.get(url, params=params, headers=self.HEADERS, timeout=10)
            if not response.is_success:
                return False
            labels = [l.get("name", "").lower() for l in response.json()]
            return any(
                "good first" in l or "help wanted" in l or "beginner" in l
                for l in labels
            )
        except Exception:
            return False

    def _scrape_gsoc_orgs(self, client: httpx.Client) -> list[dict]:
        """Scrape GSoC organization repos (seasonal)."""
        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": "topic:gsoc topic:summer-of-code",
            "sort": "stars",
            "order": "desc",
            "per_page": 30,
        }

        response = client.get(url, params=params, headers=self.HEADERS, timeout=30)
        if not response.is_success:
            logger.warning(f"GitHubOSS GSoC search: HTTP {response.status_code}")
            return []

        items = response.json().get("items", [])
        repos: list[dict] = []

        for repo in items:
            if repo.get("archived"):
                continue

            stars = repo.get("stargazers_count", 0)
            topics = repo.get("topics", []) or []
            language = repo.get("language", "") or ""
            tag_list = [t for t in topics if t != "gsoc"][:5]
            tag_list.append("gsoc")
            if language:
                tag_list.append(language.lower())

            repos.append({
                "title": f"Contribute to {repo['full_name']}",
                "type": "oss",
                "link": repo.get("html_url", ""),
                "organizer": repo.get("full_name", "").split("/")[0],
                "description": (repo.get("description", "") or "")[:1000],
                "location": "Remote",
                "prize": f"★ {stars:,}",
                "date": "",
                "tags": tag_list,
                "difficulty": "intermediate",
                "image_url": repo.get("owner", {}).get("avatar_url", ""),
                "is_closed": False,
            })

        return repos
