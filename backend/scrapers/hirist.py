import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from .base import GenericScraper, ScrapeBlockedError

logger = logging.getLogger(__name__)


class HiristScraper(GenericScraper):
    platform_name = "Hirist"
    source_key = "hirist"
    verticals = ["job"]
    BASE_URL = "https://www.hirist.tech"
    API_URLS = [
        "https://gladiator.hirist.tech/job/search",
    ]
    SEARCH_QUERIES = ["Python", "Java", "Backend", "Frontend"]
    MAX_PAGES = 3

    def scrape(self, client: httpx.Client) -> list[dict]:
        all_items: list[dict] = []
        seen_urls: set[str] = set()

        for query in self.SEARCH_QUERIES:
            for api_url in self.API_URLS:
                try:
                    items = self._try_api(client, api_url, seen_urls, query)
                    if items:
                        logger.info(f"Hirist: got {len(items)} items from API query={query!r}")
                        all_items.extend(items)
                except ScrapeBlockedError:
                    logger.warning(f"Hirist: API {api_url} blocked, trying next")
                    continue
                except Exception as e:
                    logger.warning(f"Hirist: API {api_url} failed: {e}")
                    continue
            if len(all_items) >= 50:
                break

        if all_items:
            logger.info(f"Hirist: {len(all_items)} total items from API")
            return all_items

        logger.info("Hirist: API failed, falling back to HTML scrape")
        try:
            items = self._scrape_html(client, seen_urls)
            if items:
                all_items.extend(items)
        except Exception as e:
            logger.warning(f"Hirist: HTML fallback failed: {e}")

        logger.info(f"Hirist: {len(all_items)} total items from HTML")
        return all_items

    def _try_api(self, client: httpx.Client, api_url: str, seen_urls: set[str], query: str) -> list[dict]:
        all_items: list[dict] = []

        for page in range(0, self.MAX_PAGES):
            params = {
                "query": query,
                "page": str(page),
                "minexp": "0",
                "maxexp": "1",
            }
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/search/{query}-jobs",
                "version": "2",
            }

            try:
                response = client.get(api_url, params=params, headers=headers, timeout=30)
                if response.status_code == 403:
                    raise ScrapeBlockedError(source=self.source_key, status_code=403)
                if not response.is_success:
                    logger.warning(f"Hirist API page {page}: HTTP {response.status_code}")
                    break

                data = response.json()
                jobs = self._extract_jobs_from_api(data)
                if not jobs:
                    break

                for job in jobs:
                    parsed = self._parse_api_job(job)
                    if parsed and parsed["link"] not in seen_urls:
                        seen_urls.add(parsed["link"])
                        all_items.append(parsed)

                if not data.get("hasMore"):
                    break

            except ScrapeBlockedError:
                raise
            except Exception as exc:
                logger.warning(f"Hirist API page {page} error: {exc}")
                break

        return all_items

    def _extract_jobs_from_api(self, data: dict) -> list[dict]:
        for key in ("jobs", "results", "data", "items", "list"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    def _parse_api_job(self, job: dict) -> dict | None:
        title = job.get("title") or job.get("jobTitle") or job.get("job_title") or ""
        if not title:
            return None

        link = job.get("jobDetailUrl") or job.get("url") or job.get("applyUrl") or job.get("apply_url") or job.get("jobUrl") or ""
        if link and not link.startswith("http"):
            link = f"{self.BASE_URL}{link}" if link.startswith("/") else f"{self.BASE_URL}/{link}"

        company = job.get("company") or job.get("companyName") or job.get("company_name") or ""
        company_data = job.get("companyData") or {}
        if not company and isinstance(company_data, dict):
            company = company_data.get("companyName") or company_data.get("companyNameNotAnalyzed") or ""
        if isinstance(company, dict):
            company = company.get("name") or company.get("display_name") or ""

        location = job.get("location") or job.get("city") or job.get("jobLocation") or ""
        if isinstance(location, list):
            location = ", ".join(
                loc.get("name", "") for loc in location if isinstance(loc, dict) and loc.get("name")
            )
        if isinstance(location, dict):
            location = location.get("name") or location.get("city") or ""
        other_location = job.get("otherLocation") or job.get("createdByAlias") or ""
        if other_location and other_location not in location:
            location = f"{location}, {other_location}" if location else other_location

        salary = job.get("salary") or job.get("salary_range") or job.get("salaryRange") or ""
        if not salary and not job.get("hideSal"):
            min_sal = job.get("minSal")
            max_sal = job.get("maxSal")
            if min_sal or max_sal:
                salary = f"Rs.{min_sal or 0} - Rs.{max_sal or 0}"
        if isinstance(salary, dict):
            parts = []
            if salary.get("min"):
                parts.append(f"Rs.{salary['min']}")
            if salary.get("max"):
                parts.append(f"Rs.{salary['max']}")
            salary = " - ".join(parts) if parts else ""

        skills_raw = job.get("skills") or job.get("skillTags") or job.get("keySkills") or []
        if not skills_raw and isinstance(job.get("tags"), list):
            skills_raw = [
                tag.get("name")
                for tag in job.get("tags", [])
                if isinstance(tag, dict) and tag.get("name")
            ]
        if isinstance(skills_raw, str):
            skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]
        tags = [s for s in skills_raw if s] if isinstance(skills_raw, list) else []

        experience = job.get("experience") or job.get("exp") or job.get("minExperience") or ""
        exp_min = job.get("min")
        exp_max = job.get("max")
        if isinstance(experience, (int, float)):
            experience = f"{int(experience)} yr"
        if not experience and (exp_min is not None or exp_max is not None):
            experience = f"{exp_min or 0}-{exp_max or 0} yrs"

        description = job.get("description") or job.get("jobDescription") or job.get("jd") or job.get("jobdesignation") or ""
        if description:
            if "<" in description and ">" in description:
                description = BeautifulSoup(description, "html.parser").get_text(strip=True)
            description = str(description).strip()[:1000]
        if len(description) < 20:
            description = self._fallback_description(title, company, location, experience, tags)

        posted_date = job.get("postedDate") or job.get("createdAt") or job.get("posted_on") or job.get("created") or ""
        if not posted_date and job.get("createdTime"):
            try:
                posted_date = datetime.fromtimestamp(int(job["createdTime"]) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                posted_date = ""
        deadline = self._infer_deadline(posted_date)
        image_url = ""
        if isinstance(company_data, dict):
            image_url = company_data.get("companyLogoFilePath") or company_data.get("logoPath") or company_data.get("logo") or ""
        remote = bool(job.get("workFromHome")) or "remote" in location.lower()

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
            "difficulty": self._resolve_experience_level(exp_min, exp_max, title, tags),
            "experience": experience,
            "experience_min": exp_min,
            "experience_max": exp_max,
            "employment_type": "full-time",
            "remote": remote,
            "salary_currency": "INR",
            "image_url": image_url,
            "is_closed": False,
        }

    def _scrape_html(self, client: httpx.Client, seen_urls: set[str]) -> list[dict]:
        all_items: list[dict] = []
        base_urls = [
            f"{self.BASE_URL}/search/Python-jobs?minexp=0&maxexp=1",
            f"{self.BASE_URL}/search/Java-jobs?minexp=0&maxexp=1",
            f"{self.BASE_URL}/c/backend-development-jobs",
        ]

        for base_url in base_urls:
            if len(all_items) > 50:
                break
            for page in range(1, self.MAX_PAGES + 1):
                url = f"{base_url}&page={page}" if page > 1 else base_url
                logger.info(f"Hirist HTML: fetching page {page}: {url}")

                try:
                    response = client.get(url, timeout=30)
                    if response.status_code == 403:
                        raise ScrapeBlockedError(source=self.source_key, status_code=403)
                    if not response.is_success:
                        logger.warning(f"Hirist HTML page {page}: HTTP {response.status_code}")
                        break

                    items = self._parse_html_listing(response.text)
                    if not items:
                        break

                    for item in items:
                        if item["link"] not in seen_urls:
                            seen_urls.add(item["link"])
                            all_items.append(item)

                except ScrapeBlockedError:
                    raise
                except Exception as exc:
                    logger.warning(f"Hirist HTML page {page} error: {exc}")
                    break

        return all_items

    def _parse_html_listing(self, html_text: str) -> list[dict]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(
            "div.job-card, div.job-listing-item, article.job-item, "
            "div.joblist-item, div[class*='job-card'], div[class*='job-item'], "
            "div.job_row, li.job-list-item"
        )
        if not cards:
            cards = soup.select("[data-job-id], [data-jobtitle]")

        items: list[dict] = []
        for card in cards:
            try:
                item = self._parse_html_card(card)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug(f"Hirist HTML: failed to parse card: {exc}")

        return items

    def _parse_html_card(self, card) -> dict | None:
        title_el = card.select_one(
            "a.job-title, h2 a, h3 a, .job-title a, "
            "a[class*='title'], a[href*='/job/']"
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None

        href = title_el.get("href", "") if title_el else ""
        if not href:
            link_el = card.select_one("a[href*='hirist.com']")
            href = link_el.get("href", "") if link_el else ""
        if not href:
            return None
        link = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        company_el = card.select_one(
            "span.company-name, .company-name a, .company_info a, "
            "span[class*='company'], a[class*='company']"
        )
        company = company_el.get_text(strip=True) if company_el else ""

        location_el = card.select_one(
            "span.location, .location span, .job-location, "
            "span[class*='loc'], .city"
        )
        location = location_el.get_text(strip=True) if location_el else ""

        salary_el = card.select_one(
            "span.salary, .salary span, span[class*='salary'], "
            ".job-salary, .pay"
        )
        salary = salary_el.get_text(strip=True) if salary_el else ""

        experience_el = card.select_one(
            "span.exp, .experience span, span[class*='exp'], "
            ".job-exp, .job-experience"
        )
        experience = experience_el.get_text(strip=True) if experience_el else ""

        desc_el = card.select_one(
            "p.job-description, .description, .job-desc, "
            "div[class*='desc'], p[class*='desc']"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        tags = [
            s.get_text(strip=True)
            for s in card.select(
                "div.skills span, .skill-tags span, ul.tags li, "
                "span[class*='skill'], .key-skills span"
            )
            if s.get_text(strip=True)
        ]

        posted_el = card.select_one(
            "span.date, .posted-date, span[class*='date'], "
            ".job-posted, .days-ago"
        )
        posted_text = posted_el.get_text(strip=True) if posted_el else ""
        deadline = self._infer_deadline(posted_text)
        if len(description) < 20:
            description = self._fallback_description(title, company, location, experience, tags)

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
            "difficulty": self._infer_difficulty(tags),
            "experience": experience,
            "image_url": "",
            "is_closed": False,
        }

    def _fallback_description(
        self,
        title: str,
        company: str,
        location: str,
        experience: str,
        tags: list[str],
    ) -> str:
        parts = [title]
        if company:
            parts.append(f"at {company}")
        if location:
            parts.append(f"in {location}")
        if experience:
            parts.append(f"requiring {experience} experience")
        if tags:
            parts.append("with skills in " + ", ".join(tags[:5]))
        return " ".join(parts) + "."

    def _infer_deadline(self, posted_text: str) -> str:
        if not posted_text:
            return ""
        match = re.search(r"(\d+)\s*(day|week|month|hr|hour|min)", posted_text, re.IGNORECASE)
        if not match:
            if any(kw in posted_text.lower() for kw in ("today", "just now", "just posted", "moments ago", "recently")):
                deadline = datetime.now(timezone.utc) + timedelta(days=30)
                return deadline.strftime("%Y-%m-%d")
            try:
                dt = datetime.strptime(posted_text[:10], "%Y-%m-%d")
                deadline_dt = dt + timedelta(days=30)
                return deadline_dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
            return ""
        count = int(match.group(1))
        unit = match.group(2).lower()
        if "month" in unit:
            days_ago = count * 30
        elif "week" in unit:
            days_ago = count * 7
        elif "hour" in unit or "min" in unit:
            days_ago = 0
        else:
            days_ago = count
        days_remaining = max(0, 30 - days_ago)
        deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
        return deadline.strftime("%Y-%m-%d")
