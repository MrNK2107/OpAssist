#!/usr/bin/env python
"""Run one scraper and validate parser + DB handoff shape without writing to DB."""

import argparse
import os
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from models.schemas import OpportunityType
from services.scraper_service import normalize_opportunity_type


VALID_DB_TYPES = {item.value for item in OpportunityType}


def safe_repr(value) -> str:
    return repr(value).encode("ascii", "backslashreplace").decode("ascii")


class _FakeResult:
    data = [{"id": "fake"}]


class _FakeDB:
    def __init__(self):
        self.rows = []

    @property
    def client(self):
        return True

    def upsert_opportunity(self, data: dict):
        self.rows.append(data)
        return _FakeResult()


def validate_items(items: list[dict]) -> list[str]:
    issues: list[str] = []
    for index, item in enumerate(items):
        if not item.get("title"):
            issues.append(f"item[{index}]: missing title")
        link = item.get("link")
        if not link or not str(link).startswith("http"):
            issues.append(f"item[{index}]: bad link")
        image_url = item.get("image_url")
        if image_url and not str(image_url).startswith("http"):
            issues.append(f"item[{index}]: bad image_url {image_url!r}")
        normalized_type = normalize_opportunity_type(item.get("type"))
        if normalized_type not in VALID_DB_TYPES:
            issues.append(f"item[{index}]: bad normalized type {item.get('type')!r}")
        tags = item.get("tags")
        if tags is not None and not isinstance(tags, list):
            issues.append(f"item[{index}]: tags is not a list")
        exp_min = item.get("experience_min")
        exp_max = item.get("experience_max")
        if exp_min is not None and exp_max is not None and exp_min > exp_max:
            issues.append(f"item[{index}]: experience_min > experience_max")
        for field in ("date", "deadline", "start_date", "end_date"):
            value = item.get(field)
            if value:
                try:
                    date.fromisoformat(str(value))
                except ValueError:
                    issues.append(f"item[{index}]: {field} is not ISO date {value!r}")
    return issues


def validate_quality(items: list[dict]) -> list[str]:
    issues: list[str] = []
    for index, item in enumerate(items):
        opp_type = normalize_opportunity_type(item.get("type"))
        title = str(item.get("title") or "").strip()
        organizer = str(item.get("organizer") or "").strip()
        location = str(item.get("location") or "").strip()
        description = str(item.get("description") or "").strip()

        if len(title) < 3:
            issues.append(f"item[{index}]: weak title {title!r}")
        if opp_type in {"hackathon", "internship", "job", "scholarship", "ambassador", "event"} and not organizer:
            issues.append(f"item[{index}]: missing organizer")
        if opp_type in {"hackathon", "internship", "job", "scholarship", "event"} and not location:
            issues.append(f"item[{index}]: missing location")
        if opp_type in {"hackathon", "internship", "job", "scholarship"} and len(description) < 20:
            issues.append(f"item[{index}]: weak description")
        if opp_type in {"internship", "job"}:
            tags = item.get("tags") or []
            if not tags and not item.get("employment_type") and item.get("experience_min") is None:
                issues.append(f"item[{index}]: missing tags/employment/experience detail")
    return issues


def validate_db_handoff(items: list[dict], source: str):
    from services import scraper_service

    fake = _FakeDB()
    original_db = scraper_service.db
    scraper_service.db = fake
    try:
        stats = scraper_service.upsert_opportunities(items, source)
    finally:
        scraper_service.db = original_db
    return stats, fake.rows


def main():
    parser = argparse.ArgumentParser(description="Validate one scraper without real DB writes")
    parser.add_argument("source", help="Source key from SCRAPER_REGISTRY")
    parser.add_argument("--min-items", type=int, default=1)
    parser.add_argument("--strict-quality", action="store_true", help="Fail on thin-but-structurally-valid parsed rows")
    args = parser.parse_args()

    from scrapers import SCRAPER_REGISTRY, get_scraper_class

    scraper_class = get_scraper_class(args.source)
    if not scraper_class or args.source not in SCRAPER_REGISTRY:
        print(f"Unknown source: {args.source}")
        return 2
    config = SCRAPER_REGISTRY[args.source]
    if config.status == "broken":
        print(f"source={args.source}")
        print("status=SKIP broken")
        print(f"description={config.description}")
        return 0
    if config.requires_api_key and args.source == "adzuna":
        missing = [name for name in ("ADZUNA_APP_ID", "ADZUNA_API_KEY") if not os.environ.get(name)]
        if missing:
            print(f"source={args.source}")
            print("status=SKIP missing_api_key")
            print("missing=" + ",".join(missing))
            return 0

    start = time.time()
    items = scraper_class().run()
    elapsed = time.time() - start
    issues = validate_items(items)
    if args.strict_quality:
        issues.extend(validate_quality(items))
    stats, rows = validate_db_handoff(items, args.source)
    db_issues = [
        f"db_row[{index}]: bad type {row.get('type')!r}"
        for index, row in enumerate(rows)
        if row.get("type") not in VALID_DB_TYPES
    ]
    for index, row in enumerate(rows):
        for field in ("deadline", "start_date", "end_date"):
            value = row.get(field)
            if value:
                try:
                    date.fromisoformat(str(value))
                except ValueError:
                    db_issues.append(f"db_row[{index}]: {field} is not ISO date {value!r}")
    issues.extend(db_issues)

    print(f"source={args.source}")
    print(f"items={len(items)} elapsed={elapsed:.1f}s")
    print(f"issues={len(issues)}")
    for issue in issues[:20]:
        print(f"  {issue}")
    print(f"db_stats={stats}")
    if rows:
        sample = rows[0]
        sample_keys = [
            "title",
            "type",
            "url",
            "source",
            "deadline",
            "description",
            "organizer",
            "location",
            "prize",
            "tags",
            "difficulty",
            "image_url",
        ]
        print("db_sample=" + safe_repr({key: sample.get(key) for key in sample_keys}))

    if len(items) < args.min_items:
        print(f"not enough items: expected >= {args.min_items}")
        return 1
    if issues or stats.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
