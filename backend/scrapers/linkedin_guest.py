import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, infer_deadline_from_posted

logger = logging.getLogger(__name__)


class LinkedInGuestScraper(GenericScraper):
    platform_name = "LinkedIn"
    BASE_URL = "https://www.linkedin.com"
    GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOB_DETAIL_API = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting"
    SEARCH_QUERIES = [
        "Software Engineer", "Data Scientist", "Frontend Developer",
        "Backend Developer", "Full Stack Developer", "Python Developer",
        "Java Developer", "Machine Learning Engineer",
    ]
    MAX_PAGES = 3
    RESULTS_PER_PAGE = 25
    DETAIL_TARGET = 20
    PAGE_DELAY = 1.5
    DETAIL_DELAY = 1.0
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
    }

    @property
    def item_type(self) -> str:
        return "job"

    @property
    def search_queries(self) -> list[str]:
        return self.SEARCH_QUERIES

    def scrape(self, client: httpx.Client) -> list[dict]:
        client.headers.update(self.HEADERS)
        all_items = []
        seen_ids: set[str] = set()

        for query in self.search_queries:
            for page_num in range(self.MAX_PAGES):
                start = page_num * self.RESULTS_PER_PAGE
                encoded = query.replace(" ", "%20")
                url = f"{self.GUEST_API}?keywords={encoded}&location=India&start={start}"
                try:
                    resp = client.get(url, timeout=20)
                    if resp.status_code in (401, 403, 429):
                        logger.warning(f"{self.platform_name}: blocked HTTP {resp.status_code} query={query!r}")
                        continue
                    if not resp.is_success:
                        logger.warning(f"{self.platform_name}: HTTP {resp.status_code} query={query!r} page {page_num+1}")
                        break

                    items = self._parse_listing(resp.text, query)
                    for item in items:
                        jid = item.get("_job_id")
                        if jid and jid not in seen_ids:
                            seen_ids.add(jid)
                            all_items.append(item)

                    logger.info(f"{self.platform_name}: query={query!r} page {page_num+1} -> {len(items)} items")
                    if len(items) < self.RESULTS_PER_PAGE:
                        break
                    time.sleep(self.PAGE_DELAY)
                except Exception as exc:
                    logger.warning(f"{self.platform_name}: error query={query!r} page {page_num+1}: {exc}")
                    break

            if len(all_items) >= 80:
                break

        for i, item in enumerate(all_items[: self.DETAIL_TARGET]):
            self._enrich_detail(client, item)
            if i < self.DETAIL_TARGET - 1:
                time.sleep(self.DETAIL_DELAY)

        for item in all_items:
            item.pop("_job_id", None)

        logger.info(f"{self.platform_name}: {len(all_items)} total items")
        self._log_sample_links(all_items)
        return all_items

    def _parse_listing(self, html: str, query: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("li.result-card.job-result-card")
        items = []
        for card in cards:
            try:
                item = self._parse_card(card, query)
                if item:
                    items.append(item)
            except Exception as e:
                logger.debug(f"{self.platform_name}: card parse error: {e}")
        return items

    def _parse_card(self, card, query: str) -> dict | None:
        title_el = card.select_one(".result-card__title.job-result-card__title")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        link_el = card.select_one("a.result-card__full-card-link")
        href = link_el.get("href", "") if link_el else ""
        link = href.split("?")[0] if href else ""
        if not link:
            return None
        if not link.startswith("http"):
            link = f"{self.BASE_URL}{link}"

        job_id_match = re.search(r"/jobs/view/(\d+)", link)
        job_id = job_id_match.group(1) if job_id_match else ""

        company_el = card.select_one(".result-card__subtitle.job-result-card__subtitle")
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(".job-result-card__location")
        location = location_el.get_text(strip=True) if location_el else ""

        meta_el = card.select_one(".job-result-card__meta-info")
        posted_text = meta_el.get_text(strip=True) if meta_el else ""

        image_el = card.select_one("img[data-delayed-url], img[src]")
        image_url = ""
        if image_el:
            image_url = image_el.get("data-delayed-url") or image_el.get("src", "")

        tags = self._build_tags(title, query)
        _, exp_min, exp_max = self._infer_experience(title, query)
        date_str = infer_deadline_from_posted(posted_text)

        return {
            "title": title,
            "type": self.item_type,
            "link": link,
            "organizer": company,
            "location": location,
            "description": f"{title} role at {company or 'a LinkedIn-listed employer'} in {location or 'India'}.",
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time" if self.item_type == "job" else "internship",
            "date": date_str,
            "tags": tags,
            "difficulty": self._resolve_experience_level(exp_min, exp_max, title, tags),
            "image_url": image_url,
            "is_closed": False,
            "remote": "remote" in location.lower() if location else False,
            "prize": "",
            "_job_id": job_id,
        }

    def _build_tags(self, title: str, query: str) -> list[str]:
        tags = [self.item_type]
        for raw in re.split(r"\s+", query):
            token = raw.strip().lower()
            if token and token not in tags:
                tags.append(token)
        for kw in ("fresher", "graduate", "junior", "senior", "lead", "manager", "staff", "principal", "architect"):
            if kw in title.lower() and kw not in tags:
                tags.append(kw)
        return tags

    def _infer_experience(self, title: str, query: str = "") -> tuple[str, int | None, int | None]:
        text = f"{title} {query}".lower()
        if any(term in text for term in ("principal", "staff", "architect")):
            return "senior", 8, 15
        if any(term in text for term in ("senior", "lead", "manager")):
            return "senior", 5, 10
        if any(term in text for term in ("fresher", "entry", "graduate", "junior", "trainee")):
            return "entry", 0, 1
        return "mid", 2, 5

    def _enrich_detail(self, client: httpx.Client, item: dict) -> None:
        job_id = item.get("_job_id")
        if not job_id:
            return
        url = f"{self.JOB_DETAIL_API}/{job_id}"
        try:
            resp = client.get(url, timeout=15)
            if not resp.is_success:
                return
            soup = BeautifulSoup(resp.text, "html.parser")

            desc_el = soup.select_one(".description")
            if desc_el:
                item["description"] = desc_el.get_text(" ", strip=True)[:2000]

            criteria_spans = soup.select("span.job-criteria__text")
            if len(criteria_spans) >= 1:
                level_text = criteria_spans[0].get_text(strip=True)
                if level_text:
                    item["difficulty"] = self._map_experience_level(level_text)
            if len(criteria_spans) >= 2:
                emp_type = criteria_spans[1].get_text(strip=True)
                if emp_type:
                    item["employment_type"] = emp_type

            skills = [
                li.get_text(strip=True)
                for li in soup.select("li.job-criteria__item")
                if li.get_text(strip=True)
            ]
            if skills:
                existing = item.get("tags", [])
                merged = list(dict.fromkeys(skills + existing))
                item["tags"] = merged

        except Exception as exc:
            logger.debug(f"{self.platform_name}: detail enrich error for job {job_id}: {exc}")

    @staticmethod
    def _map_experience_level(level_text: str) -> str:
        level = level_text.lower()
        if "entry" in level or "internship" in level:
            return "beginner"
        if "mid" in level or "associate" in level:
            return "intermediate"
        if "senior" in level or "director" in level or "executive" in level:
            return "advanced"
        return "intermediate"
