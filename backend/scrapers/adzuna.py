import logging
from datetime import datetime, timezone
import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)


class AdzunaScraper(GenericScraper):
    """Adzuna API scraper — entry-level tech jobs in India.

    Uses Adzuna's public API (no auth required for basic search).
    Falls back gracefully if the API is unavailable.
    """

    platform_name = "Adzuna"
    API_BASE = "https://api.adzuna.com/v1/api/in"
    SEARCH_URL = f"{API_BASE}/search/1"
    MAX_PAGES = 3
    RESULTS_PER_PAGE = 50

    # Search queries targeting fresher/entry-level tech jobs
    QUERIES = [
        "fresher software developer",
        "entry level data analyst",
        "graduate software engineer",
        "fresher python developer",
        "junior web developer",
    ]

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.QUERIES:
            items = self._search_jobs(client, query)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)

        logger.info(f"Adzuna: {len(all_items)} total items")
        return all_items

    def _search_jobs(self, client: httpx.Client, query: str) -> list[dict]:
        """Search for jobs using Adzuna API."""
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            params = {
                "app_id": "",
                "app_key": "",
                "results_per_page": self.RESULTS_PER_PAGE,
                "what": query,
                "where": "india",
                "max_days_old": 30,
                "sort_by": "date",
                "content-type": "application/json",
            }

            url = f"{self.SEARCH_URL}?page={page}"
            logger.info(f"Adzuna: searching page {page} for '{query}'")

            try:
                response = client.get(url, params=params, timeout=30)
                if response.status_code == 401:
                    logger.warning("Adzuna: API requires auth. Skipping.")
                    break
                if response.status_code == 429:
                    logger.warning("Adzuna: rate limited. Skipping.")
                    break
                if not response.is_success:
                    logger.warning(f"Adzuna page {page}: HTTP {response.status_code}")
                    break

                data = response.json()
                results = data.get("results", [])
                if not results:
                    break

                for job in results:
                    item = self._parse_job(job)
                    if item:
                        all_items.append(item)

            except Exception as exc:
                logger.warning(f"Adzuna page {page} error: {exc}")
                break

        return all_items

    def _parse_job(self, job: dict) -> dict | None:
        """Parse a single Adzuna job result."""
        title = job.get("title", "")
        if not title:
            return None

        redirect_url = job.get("redirect_url", "")
        adzuna_url = job.get("adzuna_url", "")
        link = redirect_url or adzuna_url or ""
        if not link:
            return None

        # Company
        company_data = job.get("company", {})
        company = company_data.get("display_name", "") if isinstance(company_data, dict) else ""

        # Location
        location_data = job.get("location", {})
        if isinstance(location_data, dict):
            area = location_data.get("area", [])
            location = ", ".join(area[-2:]) if area else ""
        else:
            location = ""

        # Description
        description = job.get("description", "")
        if description:
            description = description[:1000]

        # Salary
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        salary = ""
        if salary_min and salary_max:
            salary = f"₹{salary_min:,.0f} - ₹{salary_max:,.0f}/year"
        elif salary_min:
            salary = f"₹{salary_min:,.0f}/year"
        elif salary_max:
            salary = f"₹{salary_max:,.0f}/year"

        # Contract type
        contract_type = job.get("contract_type", "")
        tags = []
        if contract_type:
            tags.append(contract_type)

        # Category
        category_data = job.get("category", {})
        if isinstance(category_data, dict):
            cat_label = category_data.get("label", "")
            if cat_label:
                tags.append(cat_label)

        # Created date -> deadline inference
        created = job.get("created", "")
        deadline = ""
        if created:
            try:
                created_dt = datetime.strptime(created[:10], "%Y-%m-%d")
                # Assume 30-day listing window
                deadline_dt = created_dt + __import__("datetime").timedelta(days=30)
                deadline = deadline_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return {
            "title": title,
            "type": "job",
            "link": link,
            "organizer": company,
            "description": description,
            "location": location,
            "prize": salary,
            "date": deadline,
            "tags": tags,
            "difficulty": "beginner",
            "image_url": "",
            "is_closed": False,
        }
