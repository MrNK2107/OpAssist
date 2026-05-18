import logging
import random
from typing import List
from datetime import datetime, timezone
from abc import ABC, abstractmethod

import httpx


class GenericScraper(ABC):
    """Base class for all scrapers — uses httpx for API requests."""

    platform_name = "Generic"
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.platform_name.lower()}")

    @abstractmethod
    def scrape(self, client: httpx.Client) -> List[dict]:
        """Scrape and return list of opportunity items"""
        pass

    def run(self) -> List[dict]:
        """Main entry point for scraping"""
        self.logger.info(f"Starting {self.platform_name} scraper")
        headers = {"User-Agent": self._get_random_user_agent()}
        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            try:
                items = self.scrape(client)
            except Exception as e:
                self.logger.error(f"Scraper failed: {e}", exc_info=True)
                items = []
        self.logger.info(f"Completed {self.platform_name} scraper: {len(items)} items")
        return items

    def _get_random_user_agent(self) -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(agents)

    def _infer_difficulty(self, tags: list[str]) -> str:
        """Infer difficulty level from tags."""
        tags_lower = [t.lower() for t in tags]
        if "beginner friendly" in tags_lower or "beginner" in tags_lower:
            return "beginner"
        if "advanced" in tags_lower:
            return "advanced"
        if "intermediate" in tags_lower:
            return "intermediate"
        return "beginner"

    def _log_sample_links(self, items: List[dict]) -> None:
        sample_links = [item.get("link") for item in items[:3] if item.get("link")]
        if sample_links:
            self.logger.info(f"{self.platform_name} sample links: {sample_links}")


class ScraperResult:
    """Container for scraper results"""

    def __init__(self, platform: str, items: List[dict], errors: List[str] = None):
        self.platform = platform
        self.items = items
        self.errors = errors or []
        self.timestamp = datetime.now(timezone.utc)

    def __repr__(self):
        return f"ScraperResult(platform={self.platform}, items={len(self.items)}, errors={len(self.errors)})"
