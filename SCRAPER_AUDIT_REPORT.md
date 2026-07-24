# SCRAPER AUDIT REPORT

**Date:** 2026-07-22 | **Environment:** Windows, Python 3.12.7, Playwright 1.49.1, httpx 0.28.1

---

## REGISTRY HEALTH

**28 scrapers registered** in `SCRAPER_REGISTRY` across all verticals.
**7 scrapers imported but NOT registered** (silently orphaned).

| Vertical | Registered | Working | Empty | Failing | Unregistered |
|---|---|---|---|---|---|
| Hackathon | 11 | 11 | 0 | 0 | 0 |
| Internship | 4 | 4 | 0 | 0 | 3 |
| Job | 8 | 7 | 1 (API key) | 0 | 2 |
| Lateral | 1 | 1 | 0 | 0 | 1 |
| Other | 4 | 4 | 0 | 0 | 1 |

---

## HACKATHON SCRAPERS (11 registered, 11 OK)

| Scraper | Items | Time | Data Quality | Notes |
|---|---|---|---|---|
| **unstop** | 343 | 9.3s | ⚠️ 15 issues | 8 items have absurdly long prize text (623-1387 chars); 7 items have wrong `type: "scholarship"` instead of `hackathon`. **Needs filtering.** |
| **mlh** | 61 | 3.3s | ✅ Clean | All required fields present |
| **devpost** | 43 | 3.4s | ✅ Clean | Fast, reliable |
| **devfolio** | 23 | 49s | ✅ Clean | Slow (Playwright or API rate limits) |
| **dorahacks** | 17 | 4.1s | ✅ Clean | |
| **techgig** | 9 | 1.7s | ✅ Clean | |
| **hack2skill** | 6 | 3.5s | ✅ Clean | |
| **codechef** | 5 | 2.2s | ✅ Clean | |
| **reskilll** | 1-0 | varies | ✅ Clean | **Intermittent DNS failure** (`[Errno 11002] getaddrinfo failed`). Direct instantiation works; service layer returns empty. Needs DNS resilience. |
| **hackerearth** | 2 | 2.2s | ✅ Clean | Low volume (only 2 items) |
| **hackerrank** | 2 | 2.3s | ✅ Clean | Low volume |

**Total: ~511 items. All 11 working. Unstop needs prize truncation & type filtering.**

---

## INTERNSHIP SCRAPERS (4 registered, 4 OK + 3 unregistered)

| Scraper | Items | Time | Data Quality | Notes |
|---|---|---|---|---|
| **internshala** | 129 | 78s | ✅ Clean | Slowest scraper (78s, multi-pass). Core source. |
| **hellointern** | 20 | 2.8s | ✅ Clean | Fast, reliable |
| **letsintern** | 20-0 | varies | ✅ Clean | **Intermittent DNS failure** — same `getaddrinfo` issue as reskilll. Needs DNS retry. |
| **linkedin_internships** | 10 | 15.4s | ✅ Clean | Playwright-based |

### UNREGISTERED INTERNSHIP SCRAPERS (NOT in SCRAPER_REGISTRY)

| Scraper | Attempt Result | Impact |
|---|---|---|
| **indeed_internships** | EMPTY (DNS error) | Class exists, DNS failure on `in.indeed.com` |
| **glassdoor_internships** | EMPTY (no cards) | Playwright loads page but finds 0 job cards — Glassdoor's DOM structure likely changed |
| **twenty19** | EMPTY (no items) | HTTP request succeeds but `_parse_page` finds no matching elements — site likely redesigned |

**Action required:** Register + fix these 3. `twenty19` is probably the easiest fix (update CSS selectors).

---

## JOB SCRAPERS (8 registered, 7 OK + 1 empty)

| Scraper | Items | Time | Data Quality | Notes |
|---|---|---|---|---|
| **internshala_jobs** | 192 | 6.4s | ✅ Clean | Highest volume, fast |
| **linkedin_jobs** | 81 | 30.4s | ✅ Clean | Playwright needed but works |
| **foundit** | 60 | 15.6s | ✅ Clean | Playwright |
| **apna** | 48 | 2.8s | ✅ Clean | Fast SSR HTML |
| **hirist** | 30 | 1.9s | ✅ Clean | Fast |
| **instahyre** | 20 | 23.2s | ✅ Clean | Playwright |
| **shine** | 20 | 4.4s | ✅ Clean | Playwright |
| **adzuna** | 0 | 0.3s | - | **Requires API keys** (`ADZUNA_APP_ID`, `ADZUNA_API_KEY`). Needs env vars. |

### UNREGISTERED JOB SCRAPERS

| Scraper | Attempt Result | Impact |
|---|---|---|
| **indeed_jobs** | ⚠️ 16 items (112s) | **Actually works!** Just not registered. Playwright successfully found 16 items. **Easy fix — just add `register_scraper()` call.** |
| **naukri** | EMPTY (no cards) | Playwright found 0 job cards on all 8 URLs tried. Naukri's anti-bot measures (Cloudflare) blocking. |

---

## LATERAL / EXPERIENCED JOB SCRAPERS (1 registered, 1 OK + 1 unregistered)

| Scraper | Items | Time | Data Quality | Notes |
|---|---|---|---|---|
| **cutshort** | 9 | 97s | ✅ Clean | **Very slow** (97s). API intercept via Playwright. At least `experience_min/max` and `remote` fields populated. |
| **wellfound** | 0 | 188s | - | **Unregistered + empty.** Playwright tried 10 job categories on AngelList/Wellfound, found 0 jobs. Site likely restructured. |

---

## CRITICAL ISSUES

### 1. Unstop — Type Pollution
`test_scrapers.py` reports: `7 items with invalid type 'scholarship'`
Unstop returns both hackathons AND scholarships in its API response. The scraper doesn't filter by type. Fix in `backend/scrapers/unstop.py`.

### 2. Unstop — Long Prize Text
`8 items with prize > 500 chars` (up to 1,387 chars). The `base.py` `_sanitize_prize()` method handles Unicode but does **not** truncate. Need a max-length guard.

### 3. 7 Unregistered Scrapers
These classes exist but are excluded from the runtime. `indeed_jobs` is **fully functional** (16 items) and just needs a registration call. The others need selector fixes first.

### 4. DNS Intermittency
`reskilll` and `letsintern` fail sporadically with `[Errno 11002] getaddrinfo failed` when run through `services.scraper_service.run_scraper()`. The base class retry doesn't catch DNS errors as a `ScrapeError` subclass — DNS errors are raw `httpx.ConnectError`. The `_run_with_retry` catches generic `Exception` but only returns `[]` without retry. Need to add DNS retry logic.

### 5. Slow Scrapers

| Scraper | Time | Bottleneck |
|---|---|---|
| wellfound | 188s | 10 Playwright page loads, 0 results |
| cutshort | 97s | Single Playwright with API intercept |
| naukri | 173s | 8 Playwright page loads, 0 results |
| indeed_jobs | 112s | 3 Playwright page loads |
| internshala | 78s | HTTP multi-pass with detail fetches |
| devfolio | 49s | Likely API rate limits |
| glassdoor | 24s | Playwright with scroll + wait |

---

## DATA QUALITY METRICS

| Metric | Score |
|---|---|
| **Required fields present** (title, type, link) | ✅ 100% of non-empty scrapers |
| **Valid opportunity types** | ⚠️ 7 unstop items wrong type |
| **Reasonable prize length** | ⚠️ 8 unstop items too long |
| **Lateral fields** (exp_min/max, remote, salary_currency, employment_type) | ✅ Present in cutshort, some jobs |
| **Date/Deadline present** | ✅ Most hackathons; ⚠️ Many internships/jobs missing dates |

---

## RECOMMENDATIONS (Priority Ordered)

1. **Register orphaned `indeed_jobs`** — already works (16 items), just needs `register_scraper()` in `__init__.py`
2. **Fix unstop filtering** — add `type == "hackathon"` guard in `backend/scrapers/unstop.py`
3. **Truncate prizes > 500 chars** — add truncation in `base.py` `_sanitize_prize()`
4. **Fix DNS intermittent failures** — add `httpx.ConnectError` to retryable errors in `base.py` `_run_with_retry()`
5. **Fix twenty19 selectors** — update CSS selectors in `backend/scrapers/twenty19.py` for current site DOM
6. **Fix indeed_internships** — DNS resolution issue or update Playwright selectors
7. **Fix glassdoor_internships** — update Playwright selectors for current DOM
8. **Fix naukri** — investigate Cloudflare bypass or mark as broken
9. **Fix wellfound** — update selectors for current AngelList/Wellfound DOM
10. **Set up Adzuna API keys** — `ADZUNA_APP_ID` and `ADZUNA_API_KEY` in `.env`
11. **Add timeout configs** — wellfound (188s), naukri (173s), indeed_jobs (112s) should have shorter timeouts
