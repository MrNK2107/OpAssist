"""
Adzuna API Scraper — India fresher / entry-level jobs.

═══════════════════════════════════════════════════════════
Setup Instructions (Free-Tier API Key)
═══════════════════════════════════════════════════════════

1. Go to https://developer.adzuna.com/ and sign up for a free account.
2. After logging in, you'll receive an **Application ID** and an **API Key**
   — both are required.
3. The free tier gives you **500 API calls per month** (enough for daily runs
   with the 20 queries x ~3 pages = ~60 requests).

Set these environment variables before running:

    export ADZUNA_APP_ID="your_app_id_here"
    export ADZUNA_API_KEY="your_api_key_here"

On Windows (PowerShell):

    $env:ADZUNA_APP_ID = "your_app_id_here"
    $env:ADZUNA_API_KEY = "your_api_key_here"

Or pass them directly to the constructor:

    AdzunaScraper(app_id="...", api_key="...")

═══════════════════════════════════════════════════════════
"""

import logging
import os
from datetime import datetime, timedelta
from itertools import cycle

import httpx

from .base import GenericScraper

logger = logging.getLogger(__name__)

# ── India cities to cycle through for location variety ──
INDIA_CITIES = [
    "india",
    "bangalore",
    "mumbai",
    "delhi",
    "hyderabad",
    "pune",
    "chennai",
    "kolkata",
]


class AdzunaScraper(GenericScraper):
    """Adzuna API scraper — fresher / entry-level jobs across India.

    Requires ADZUNA_APP_ID and ADZUNA_API_KEY env vars.
    Falls back gracefully if the API is unavailable.
    """

    platform_name = "Adzuna"
    source_key = "adzuna"
    verticals = ["job"]
    requires_api_key = True
    API_BASE = "https://api.adzuna.com/v1/api/jobs"
    MAX_PAGES = 3
    RESULTS_PER_PAGE = 50

    # ── 20 India-specific fresher queries (10 tech + 10 non-tech) ──
    QUERIES = [
        # Tech
        "fresher software developer",
        "entry level data analyst",
        "graduate software engineer",
        "fresher python developer",
        "junior web developer",
        "fresher java developer",
        "fresher frontend developer",
        "fresher backend developer",
        "graduate trainee",
        "fresher devops engineer",
        # Non-tech
        "fresher business analyst",
        "fresher digital marketing",
        "fresher content writer",
        "fresher hr",
        "fresher sales",
        "fresher customer support",
        "fresher graphic designer",
        "fresher finance intern",
        "management trainee",
        "fresher data entry",
    ]

    def __init__(self, app_id: str = "", api_key: str = ""):
        super().__init__()
        self.app_id = app_id or os.environ.get("ADZUNA_APP_ID", "")
        self.api_key = api_key or os.environ.get("ADZUNA_API_KEY", "")
        self._city_cycler = cycle(INDIA_CITIES)

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        if not self.app_id or not self.api_key:
            logger.warning("Adzuna: ADZUNA_APP_ID and ADZUNA_API_KEY not configured. Skipping.")
            return []

        for query in self.QUERIES:
            # Cycle to next city so queries are spread across locations
            city = next(self._city_cycler)
            items = self._search_jobs(client, query, city)
            for item in items:
                if item["link"] not in seen_urls:
                    seen_urls.add(item["link"])
                    all_items.append(item)

        logger.info(f"Adzuna: {len(all_items)} total items from {len(self.QUERIES)} queries")
        return all_items

    def _search_jobs(self, client: httpx.Client, query: str, city: str) -> list[dict]:
        """Search for jobs using the Adzuna API."""
        all_items: list[dict] = []

        for page in range(1, self.MAX_PAGES + 1):
            params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "results_per_page": self.RESULTS_PER_PAGE,
                "what": query,
                "where": city,
                "max_days_old": 30,
                "sort_by": "date",
                "content-type": "application/json",
            }

            # URL format: /v1/api/jobs/{country}/search/{page}
            url = f"{self.API_BASE}/in/search/{page}"
            logger.info(f"Adzuna: searching page {page} for '{query}' in {city}")

            try:
                response = client.get(url, params=params, timeout=30)
                if response.status_code == 401:
                    logger.warning("Adzuna: auth failed — check ADZUNA_APP_ID and ADZUNA_API_KEY")
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

                # Guard: fewer results than page size means this is the last page
                if len(results) < self.RESULTS_PER_PAGE:
                    logger.debug(f"Adzuna: only {len(results)} results on page {page} — last page reached")

                for job in results:
                    item = self._parse_job(job)
                    if item:
                        all_items.append(item)

                # Stop paginating if we received fewer results than the page size
                if len(results) < self.RESULTS_PER_PAGE:
                    break

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

        # ── Company ──
        company_data = job.get("company", {})
        company = company_data.get("display_name", "") if isinstance(company_data, dict) else ""

        # ── Location ──
        location_data = job.get("location", {})
        if isinstance(location_data, dict):
            area = location_data.get("area", [])
            location = ", ".join(area[-2:]) if area else ""
        else:
            location = ""

        # ── Description ──
        description = job.get("description", "")
        if description:
            description = description[:1000]

        # ── Salary ──
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        salary_is_predicted = job.get("salary_is_predicted", False)

        salary = ""
        if salary_min is not None and salary_max is not None:
            salary = f"Rs.{salary_min:,.0f} - Rs.{salary_max:,.0f}/year"
        elif salary_min is not None:
            salary = f"Rs.{salary_min:,.0f}/year"
        elif salary_max is not None:
            salary = f"Rs.{salary_max:,.0f}/year"

        if salary and salary_is_predicted:
            salary = f"{salary} (estimated)"

        # ── Tags ──
        tags = []

        contract_type = job.get("contract_type", "")
        if contract_type:
            # Normalise: "permanent" → "Full-time", "contract" → "Contract", etc.
            norm = contract_type.lower().strip()
            tag_map = {
                "permanent": "full-time",
                "full_time": "full-time",
                "part_time": "part-time",
                "contract": "contract",
                "internship": "internship",
            }
            tags.append(tag_map.get(norm, contract_type))

        category_data = job.get("category", {})
        if isinstance(category_data, dict):
            cat_label = category_data.get("label", "")
            if cat_label:
                tags.append(cat_label)
            cat_tag = category_data.get("tag", "")
            if cat_tag and cat_tag != cat_label:
                tags.append(cat_tag)

        # Infer difficulty from title / tags
        difficulty = self._resolve_difficulty(title, tags)

        # ── Created date → deadline inference ──
        created = job.get("created", "")
        deadline = ""
        if created:
            try:
                created_dt = datetime.strptime(created[:10], "%Y-%m-%d")
                deadline_dt = created_dt + timedelta(days=30)
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
            "difficulty": difficulty,
            "image_url": "",
            "is_closed": False,
        }

    @staticmethod
    def _resolve_difficulty(title: str, tags: list[str]) -> str:
        """Infer difficulty from the job title and tags."""
        title_lower = title.lower()
        combined = title_lower + " " + " ".join(t.lower() for t in tags)

        if any(kw in combined for kw in ("intern", "internship", "trainee")):
            return "beginner"
        if any(kw in combined for kw in ("fresher", "entry level", "junior", "graduate")):
            return "beginner"
        if any(kw in combined for kw in ("senior", "lead", "principal", "manager", "head of")):
            return "advanced"
        return "beginner"
