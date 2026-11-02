"""Offline scraper parser tests.

Every test here runs against saved HTML/JSON fixtures in ``tests/fixtures/scrapers``.
Real network access is blocked for the whole module (see ``_no_network``), so a
scraper that silently tries to hit the internet fails loudly instead of flaking.

The fixtures mirror the DOM / API shapes each site served when the selectors
were written (SCRAPER_AUDIT_REPORT.md). If a site redesigns, capture a fresh
page into the fixture and update the expectations.
"""
from __future__ import annotations

import json
import re
import socket
from pathlib import Path

import httpx
import pytest

from scrapers import SCRAPER_REGISTRY, get_scraper_class
from scrapers.base import GenericScraper, ScrapeBlockedError
from scrapers.glassdoor_internships import GlassdoorInternshipsScraper
from scrapers.indeed_internships import IndeedInternshipsScraper
from scrapers.naukri import NaukriScraper
from scrapers.twenty19 import Twenty19Scraper
from scrapers.unstop import UnstopScraper
from scrapers.wellfound import WellfoundScraper

FIXTURES = Path(__file__).parent / "fixtures" / "scrapers"
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_KEYS = {"title", "type", "link"}


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Fail any attempt to open a real socket connection."""

    def guard(*args, **kwargs):
        raise RuntimeError("network access is not allowed in offline scraper tests")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)
    monkeypatch.setattr(socket, "getaddrinfo", guard)


def assert_well_formed(items: list[dict], expected_type: str) -> None:
    links = [i["link"] for i in items]
    assert len(links) == len(set(links)), "duplicate links"
    for item in items:
        assert REQUIRED_KEYS <= item.keys()
        assert item["title"].strip()
        assert item["type"] == expected_type
        assert item["link"].startswith("https://")
        if item.get("date"):
            assert ISO_DATE.match(item["date"]), item["date"]


# ---------------------------------------------------------------------------
# Naukri
# ---------------------------------------------------------------------------

class TestNaukriParser:
    def setup_method(self):
        self.items = NaukriScraper()._parse_listing_page(fixture_text("naukri_listing.html"))

    def test_parses_each_job_tuple_once(self):
        # broad fallback selectors (div[class*='job']) match nested wrappers too
        assert [i["title"] for i in self.items] == ["Graduate Engineer Trainee", "Data Analyst Intern"]
        assert_well_formed(self.items, "job")

    def test_fields(self):
        first = self.items[0]
        assert first["organizer"] == "Acme Pvt Ltd"
        assert first["location"] == "Bengaluru"
        assert first["prize"] == "3-4.5 Lacs PA"
        assert first["salary_currency"] == "INR"
        assert (first["experience_min"], first["experience_max"]) == (0, 1)
        assert first["description"].startswith("Freshers with B.Tech")

    def test_tags_are_individual_skills(self):
        assert self.items[0]["tags"] == ["Python", "SQL"]

    def test_relative_link_is_absolutized(self):
        assert self.items[1]["link"].startswith("https://www.naukri.com/job-listings-data-analyst-intern")

    def test_experience_is_case_insensitive(self):
        assert (self.items[1]["experience_min"], self.items[1]["experience_max"]) == (0, 2)

    @pytest.mark.parametrize("text,expected", [
        ("0-1 Yrs", (0, 1)),
        ("2 to 5 years", (2, 5)),
        ("3 Yrs", (3, 5)),
        ("", (None, None)),
        ("Fresher", (None, None)),
    ])
    def test_parse_experience(self, text, expected):
        assert NaukriScraper._parse_experience(text) == expected

    def test_pagination_url_scheme(self):
        base = "https://www.naukri.com/fresher-jobs"
        assert NaukriScraper._page_url(base, 1) == base
        assert NaukriScraper._page_url(base, 2) == f"{base}-2"
        assert NaukriScraper._page_url(base, 3) == f"{base}-3"

    def test_no_seed_url_is_a_page_of_another(self):
        urls = NaukriScraper.LISTING_URLS
        for a in urls:
            for b in urls:
                assert not re.fullmatch(re.escape(a) + r"-\d+", b), f"{b} is a page of {a}"

    def test_empty_page_yields_nothing(self):
        assert NaukriScraper()._parse_listing_page("<html><body></body></html>") == []

    def test_scrape_falls_back_to_playwright_when_blocked(self, monkeypatch):
        transport = httpx.MockTransport(lambda request: httpx.Response(403, text="blocked"))
        scraper = NaukriScraper()
        sentinel = [{"title": "from playwright", "type": "job", "link": "https://www.naukri.com/x"}]
        monkeypatch.setattr(scraper, "_with_playwright", lambda fn, *a, **k: sentinel)
        with httpx.Client(transport=transport) as client:
            assert scraper.scrape(client) == sentinel

    def test_scrape_via_httpx_uses_fixture(self, monkeypatch):
        html = fixture_text("naukri_listing.html")
        seen_urls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen_urls.append(str(request.url))
            if request.url.path.endswith("-2") or request.url.path.endswith("-3"):
                return httpx.Response(200, text="<html></html>")
            return httpx.Response(200, text=html)

        scraper = NaukriScraper()
        monkeypatch.setattr(scraper, "_with_playwright", lambda *a, **k: pytest.fail("should not need Playwright"))
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            items = scraper.scrape(client)
        # same two jobs on every seed URL -> deduped across URLs
        assert len(items) == 2
        assert "https://www.naukri.com/fresher-jobs-2" in seen_urls
        assert not any(u.endswith("/2") for u in seen_urls)


# ---------------------------------------------------------------------------
# Indeed internships
# ---------------------------------------------------------------------------

class TestIndeedInternshipsParser:
    def setup_method(self):
        self.items = IndeedInternshipsScraper()._parse_listing_page(fixture_text("indeed_internships.html"))

    def test_cards(self):
        assert [i["title"] for i in self.items] == ["Marketing Intern", "Software Development Intern"]
        assert_well_formed(self.items, "internship")

    def test_uses_indian_domain_for_relative_links(self):
        assert self.items[0]["link"] == "https://in.indeed.com/rc/clk?jk=abc123&from=serp"
        assert self.items[1]["link"] == "https://in.indeed.com/viewjob?jk=def456"

    def test_location_is_not_polluted_by_company_wrapper(self):
        assert self.items[0]["location"] == "Mumbai, Maharashtra"
        assert self.items[0]["organizer"] == "Initech Solutions"

    def test_description_is_snippet_not_salary(self):
        assert self.items[0]["description"] == "Assist with social media campaigns."
        assert "10,000" in self.items[0]["prize"]


# ---------------------------------------------------------------------------
# Glassdoor internships
# ---------------------------------------------------------------------------

class TestGlassdoorInternshipsParser:
    def setup_method(self):
        self.items = GlassdoorInternshipsScraper()._parse_listing_page(fixture_text("glassdoor_internships.html"))

    def test_cards(self):
        assert [i["title"] for i in self.items] == ["Research Intern", "Design Intern"]
        assert_well_formed(self.items, "internship")

    def test_fields(self):
        first = self.items[0]
        assert first["organizer"] == "Umbrella Corp"
        assert first["location"] == "Pune"
        assert "12K" in first["prize"]
        assert first["description"] == "Work with the R&D team on lab automation."
        assert ISO_DATE.match(first["date"])

    def test_relative_link_is_absolutized(self):
        assert self.items[1]["link"].startswith("https://www.glassdoor.co.in/job-listing/design-intern")


# ---------------------------------------------------------------------------
# Twenty19
# ---------------------------------------------------------------------------

class TestTwenty19Parser:
    def setup_method(self):
        self.items = Twenty19Scraper()._parse_page(fixture_text("twenty19_listing.html"))

    def test_cards(self):
        assert [i["title"] for i in self.items] == ["Content Writing Intern", "Web Development Intern"]
        assert_well_formed(self.items, "internship")

    def test_fields(self):
        first = self.items[0]
        assert first["organizer"] == "Wayne Enterprises"
        assert first["location"] == "Chennai"
        assert first["prize"] == "Rs. 8,000 /month"
        assert first["duration"] == "3 Months"
        assert first["tags"] == ["Writing", "SEO"]
        assert first["link"] == "https://www.twenty19.com/internship/content-writing-intern-wayne-enterprises-123"

    def test_unrelated_markup_yields_no_items(self):
        assert Twenty19Scraper()._parse_page("<html><body><p>Maintenance</p></body></html>") == []


# ---------------------------------------------------------------------------
# Wellfound
# ---------------------------------------------------------------------------

class TestWellfoundParser:
    def test_jsonld_itemlist_with_listitem_wrappers(self):
        items = WellfoundScraper()._parse_listing_page(fixture_text("wellfound_jsonld.html"), "")
        assert [i["title"] for i in items] == ["Senior Backend Engineer", "Frontend Engineer"]
        assert_well_formed(items, "job")
        first = items[0]
        assert first["organizer"] == "Pied Piper"
        assert first["location"] == "Bengaluru, KA"
        assert first["description"] == "Build APIs"
        assert first["prize"] == "$40,000 - $60,000/year"
        assert "FULL_TIME" in first["tags"]

    def test_role_tag_only_when_role_known(self):
        items = WellfoundScraper()._parse_listing_page(fixture_text("wellfound_jsonld.html"), "data-scientist")
        assert items[1]["tags"] == ["Data Scientist"]
        items = WellfoundScraper()._parse_listing_page(fixture_text("wellfound_jsonld.html"), "")
        assert items[1]["tags"] == []

    def test_html_card_fallback(self):
        items = WellfoundScraper()._parse_listing_page(fixture_text("wellfound_cards.html"), "")
        assert len(items) == 1
        job = items[0]
        assert job["title"] == "Staff Engineer"
        assert job["link"] == "https://wellfound.com/jobs/333-staff-engineer"
        assert job["organizer"] == "Raviga Capital"
        assert job["location"] == "Remote (India)"
        # salary must come from the compensation element, not "companyName"
        assert "40L" in job["prize"]

    def test_blocked_error_is_not_swallowed(self):
        class Page:
            url = "https://wellfound.com/jobs"

            def add_init_script(self, *_):
                pass

            def set_extra_http_headers(self, *_):
                pass

            def goto(self, *a, **k):
                raise ScrapeBlockedError(source="wellfound", status_code=403)

        with pytest.raises(ScrapeBlockedError):
            WellfoundScraper()._playwright_scrape(Page())


# ---------------------------------------------------------------------------
# Unstop (JSON API)
# ---------------------------------------------------------------------------

class TestUnstopParser:
    def setup_method(self):
        self.payload = json.loads(fixture_text("unstop_search.json"))

    def _parse_all(self, mapped_type="hackathon"):
        s = UnstopScraper()
        return [x for x in (s._parse_item(h, mapped_type) for h in self.payload["data"]["data"]) if x]

    def test_skips_expired_and_untitled(self):
        assert [i["title"] for i in self._parse_all()] == ["CodeSprint 2099", "Campus Hack"]

    def test_fields(self):
        first, second = self._parse_all()
        assert first["link"] == "https://unstop.com/hackathons/codesprint-2099-1"
        assert first["date"] == "2099-12-31"
        assert first["location"] == "Remote"
        assert first["organizer"] == "IIT Example"
        assert first["tags"] == ["AI", "Web", "Engineering", "Python"]
        assert first["prize"] == "Winner: 50000 | Runner-up: 25000 | Goodies"
        assert first["description"] == "Build something cool ."
        assert second["link"] == "https://unstop.com/hackathons/campus-hack-4"
        assert second["location"] == "Delhi, India"

    def test_scholarships_not_fetched(self):
        # audit critical issue #1: scholarships leaked into the hackathon vertical
        assert "scholarships" not in UnstopScraper.OPPORTUNITY_TYPES
        assert set(UnstopScraper.OPPORTUNITY_TYPES.values()) <= {"hackathon", "internship"}

    def test_fetch_type_with_mock_transport(self):
        body = fixture_text("unstop_search.json")
        requested: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested.append(dict(request.url.params))
            return httpx.Response(200, text=body, headers={"content-type": "application/json"})

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            items = UnstopScraper()._fetch_type(client, "hackathons", "hackathon")
        assert [i["title"] for i in items] == ["CodeSprint 2099", "Campus Hack"]
        assert all(i["type"] == "hackathon" for i in items)
        # total=4 < per_page=50 -> a single request
        assert len(requested) == 1
        assert requested[0]["opportunity"] == "hackathons"
        assert requested[0]["oppstatus"] == "open"


# ---------------------------------------------------------------------------
# Base helpers + registry
# ---------------------------------------------------------------------------

class _Dummy(GenericScraper):
    platform_name = "Dummy"
    source_key = "dummy"
    base_delay = 0

    def scrape(self, client):
        return []


class TestBaseHelpers:
    def test_sanitize_prize_truncates_long_text(self):
        out = _Dummy()._sanitize_prize("₹" + "x" * 2000)
        assert len(out) == 500
        assert out.startswith("Rs.")
        assert out.endswith("...")

    def test_sanitize_prize_keeps_short_text(self):
        assert _Dummy()._sanitize_prize("₹ 10,000") == "Rs. 10,000"

    def test_dedupe_by_link(self):
        items = [{"link": "a"}, {"link": "b"}, {"link": "a"}, {"link": ""}, {}]
        assert GenericScraper._dedupe_by_link(items) == [{"link": "a"}, {"link": "b"}]

    def test_leaf_texts_and_select_first(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            "<div class='tags'><span class='tag'>A</span><span class='tag'>B</span>"
            "<span class='tag'>A</span></div><p class='x-location'>wrong</p><p data-loc>right</p>",
            "html.parser",
        )
        assert GenericScraper._leaf_texts(soup.select("[class*='tag']")) == ["A", "B"]
        assert GenericScraper._select_first(soup, "[data-loc]", "[class*='location']").text == "right"
        assert GenericScraper._select_first(soup, ".missing") is None

    def test_connect_error_is_retried(self, monkeypatch):
        scraper = _Dummy()
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise httpx.ConnectError("[Errno 11002] getaddrinfo failed")
            return [{"title": "ok", "type": "hackathon", "link": "https://x"}]

        monkeypatch.setattr(scraper, "_try_scrape", flaky)
        monkeypatch.setattr(scraper, "_backoff", lambda attempt: None)
        assert scraper.run()[0]["title"] == "ok"
        assert calls["n"] == 3

    @pytest.mark.parametrize("key", ["indeed_jobs", "naukri", "wellfound", "glassdoor_internships", "twenty19", "indeed_internships"])
    def test_previously_orphaned_scrapers_are_registered(self, key):
        assert key in SCRAPER_REGISTRY

    def test_every_registered_scraper_has_a_class(self):
        missing = [k for k in SCRAPER_REGISTRY if get_scraper_class(k) is None]
        assert missing == []
