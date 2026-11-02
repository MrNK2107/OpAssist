import logging
import random
import re
import time
from typing import List, Optional, Literal
from datetime import datetime, timedelta, timezone
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx


Vertical = Literal["hackathon", "internship", "job", "job_lateral", "scholarship", "ambassador", "fellowship", "event"]
ScraperPriority = Literal["critical", "high", "medium", "low"]
ScraperStatus = Literal["active", "unstable", "broken"]


@dataclass
class SourceConfig:
    name: str
    verticals: List[Vertical]
    priority: ScraperPriority = "medium"
    status: ScraperStatus = "active"
    interval_hours: int = 12
    max_pages: int = 3
    timeout: int = 30
    requires_playwright: bool = False
    requires_api_key: bool = False
    description: str = ""


SCRAPER_REGISTRY: dict[str, SourceConfig] = {}


def register_scraper(source_key: str, config: SourceConfig):
    SCRAPER_REGISTRY[source_key] = config


def get_scrapers_for_vertical(vertical: Vertical) -> list[tuple[str, SourceConfig]]:
    return [(k, v) for k, v in SCRAPER_REGISTRY.items() if vertical in v.verticals]


def get_all_source_keys() -> list[str]:
    return list(SCRAPER_REGISTRY.keys())


class ScrapeError(Exception):
    def __init__(self, message: str, source: str = "", recoverable: bool = True):
        self.source = source
        self.recoverable = recoverable
        super().__init__(message)


class ScrapeBlockedError(ScrapeError):
    def __init__(self, source: str = "", status_code: int = 403):
        self.status_code = status_code
        super().__init__(f"Scraper blocked ({status_code})", source=source, recoverable=False)


class ScrapeAuthError(ScrapeError):
    def __init__(self, source: str = ""):
        super().__init__(f"Scraper authentication failed", source=source, recoverable=False)


class ScrapeRateLimitError(ScrapeError):
    def __init__(self, source: str = "", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s", source=source, recoverable=True)


PLAYWRIGHT_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
"""


def infer_deadline_from_posted(posted_text: str, default_days: int = 30) -> str:
    """Unified deadline inference from 'posted X days/weeks/months ago' text.

    All scrapers should use this instead of duplicating the logic.
    Falls back to 'default_days from now' for recently posted items,
    or '' for unparseable text.
    """
    if not posted_text:
        return ""
    text = posted_text.lower().strip()

    if re.search(r"today|just now|just posted|just launched|moments? ago|recently", text):
        return (datetime.now(timezone.utc) + timedelta(days=default_days)).strftime("%Y-%m-%d")

    if "yesterday" in text:
        return (datetime.now(timezone.utc) + timedelta(days=default_days - 1)).strftime("%Y-%m-%d")

    if re.search(r"30\+?\s*d|over a month|month\s*ago", text):
        return (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    match = re.search(r"(\d+)\s*(day|week|month|hr|hour|min)", text)
    if not match:
        return ""

    count = int(match.group(1))
    unit = match.group(2).lower()

    if "month" in unit:
        days_ago = count * 30
    elif "week" in unit:
        days_ago = count * 7
    elif "hr" in unit or "hour" in unit or "min" in unit:
        days_ago = 0
    else:
        days_ago = count

    days_remaining = max(0, default_days - days_ago)
    return (datetime.now(timezone.utc) + timedelta(days=days_remaining)).strftime("%Y-%m-%d")


class GenericScraper(ABC):
    platform_name = "Generic"
    source_key = "generic"
    verticals: List[Vertical] = []
    requires_playwright = False
    requires_api_key = False
    max_retries = 3
    base_delay = 2.0

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.source_key}")
        self._playwright_page = None

    @abstractmethod
    def scrape(self, client: httpx.Client) -> List[dict]:
        pass

    def scrape_playwright(self, page) -> List[dict]:
        raise NotImplementedError(f"{self.platform_name} does not support Playwright fallback")

    def run(self) -> List[dict]:
        self.logger.info(f"Starting {self.platform_name} scraper (verticals: {self.verticals})")
        items = self._run_with_retry()
        for item in items:
            raw = item.get("prize")
            if raw:
                item["prize"] = self._sanitize_prize(raw)
            if not item.get("source_platform"):
                item["source_platform"] = self.platform_name
        self.logger.info(f"Completed {self.platform_name}: {len(items)} items")
        return items

    def _run_with_retry(self) -> List[dict]:
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._try_scrape()
            except ScrapeBlockedError as e:
                if self.requires_playwright or attempt < self.max_retries:
                    self.logger.warning(f"Attempt {attempt}/{self.max_retries} blocked ({e.status_code})")
                    last_error = e
                    if attempt < self.max_retries:
                        self._backoff(attempt)
                    continue
                self.logger.warning(f"All attempts blocked, scraper may need Playwright")
                return []
            except ScrapeAuthError as e:
                self.logger.error(f"Auth failed: {e}")
                return []
            except ScrapeRateLimitError as e:
                self.logger.warning(f"Rate limited on attempt {attempt}")
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(min(e.retry_after, 30))
                continue
            except ScrapeError as e:
                self.logger.warning(f"Attempt {attempt} failed: {e}")
                last_error = e
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue
            except httpx.ConnectError as e:
                self.logger.warning(f"DNS/connect error on attempt {attempt}: {e}")
                last_error = e
                if attempt < self.max_retries:
                    self._backoff(attempt)
                continue
            except Exception as e:
                self.logger.error(f"Scraper failed: {e}", exc_info=True)
                return []
        self.logger.error(f"All {self.max_retries} attempts exhausted: {last_error}")
        return []

    def _try_scrape(self) -> List[dict]:
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            return self.scrape(client)

    def _backoff(self, attempt: int) -> None:
        delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
        self.logger.info(f"Backing off {delay:.1f}s before retry {attempt + 1}")
        time.sleep(delay)

    def _with_playwright(self, fn, extra_headers: dict | None = None):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.logger.warning("Playwright not installed, cannot use fallback")
            return []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self._get_random_user_agent(),
                    viewport={"width": 1920, "height": 1080},
                    extra_http_headers=extra_headers or {},
                )
                page = context.new_page()
                page.add_init_script(PLAYWRIGHT_STEALTH_SCRIPT)
                result = fn(page)
                browser.close()
                return result
        except Exception as e:
            self.logger.error(f"Playwright fallback failed: {e}")
            return []

    def _get_random_user_agent(self) -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(agents)

    def _resolve_experience_level(self, exp_min: int | None, exp_max: int | None, title: str = "", tags: list[str] | None = None) -> str:
        combined = title.lower() + " " + " ".join(t.lower() for t in (tags or []))
        if any(kw in combined for kw in ("senior", "lead", "principal", "staff", "architect", "head of", "manager", "director")):
            return "advanced"
        if any(kw in combined for kw in ("fresher", "entry", "junior", "graduate", "trainee", "intern")):
            return "beginner"
        if exp_min is not None:
            if exp_min >= 5:
                return "advanced"
            if exp_min >= 2:
                return "intermediate"
        return "beginner"

    def _infer_difficulty(self, tags: list[str]) -> str:
        tags_lower = [t.lower() for t in tags]
        if "beginner friendly" in tags_lower or "beginner" in tags_lower:
            return "beginner"
        if "advanced" in tags_lower:
            return "advanced"
        if "intermediate" in tags_lower:
            return "intermediate"
        return "beginner"

    def _sanitize_prize(self, prize: str) -> str:
        if not prize:
            return prize
        prize = prize.replace("\u20b9", "Rs.").replace("\u20a8", "Rs.")
        if len(prize) > 500:
            prize = prize[:497] + "..."
        return prize

    @staticmethod
    def _dedupe_by_link(items: List[dict]) -> List[dict]:
        """Drop items whose link was already seen (keeps first occurrence).

        Broad fallback selectors (e.g. ``div[class*='job']``) match both a card
        and its nested wrappers, which would otherwise yield duplicate items.
        """
        seen: set = set()
        out: List[dict] = []
        for item in items:
            link = item.get("link")
            if not link or link in seen:
                continue
            seen.add(link)
            out.append(item)
        return out

    @staticmethod
    def _select_first(card, *selectors: str):
        """Return the first element matching the selectors *in priority order*.

        ``card.select_one("a, b")`` returns whichever matches first in document
        order, so a broad fallback selector can beat a precise one.
        """
        for sel in selectors:
            el = card.select_one(sel)
            if el is not None:
                return el
        return None

    @staticmethod
    def _leaf_texts(elements) -> List[str]:
        """Unique, non-empty texts of matched elements that do not contain other matches.

        Broad selectors like ``[class*='tag']`` match a tag container *and* its
        children; taking the container text would concatenate tags ("PythonSQL").
        """
        ids = {id(e) for e in elements}
        texts: List[str] = []
        for el in elements:
            if any(id(d) in ids for d in el.find_all(True)):
                continue
            text = el.get_text(strip=True)
            if text and text not in texts:
                texts.append(text)
        return texts

    def _log_sample_links(self, items: List[dict]) -> None:
        sample_links = [item.get("link") for item in items[:3] if item.get("link")]
        if sample_links:
            self.logger.info(f"{self.platform_name} sample links: {sample_links}")


class ScraperResult:
    def __init__(self, platform: str, items: List[dict], errors: List[str] = None):
        self.platform = platform
        self.items = items
        self.errors = errors or []
        self.timestamp = datetime.now(timezone.utc)

    def __repr__(self):
        return f"ScraperResult(platform={self.platform}, items={len(self.items)}, errors={len(self.errors)})"
