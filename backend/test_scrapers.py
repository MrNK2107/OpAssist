"""Scraper verification harness — runs representative scrapers and validates output."""

import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("test_harness")

REQUIRED_FIELDS = {"title", "type", "link"}
OPTIONAL_FIELDS = {
    "description", "organizer", "location", "prize", "date",
    "tags", "difficulty", "image_url", "is_closed",
    "salary_currency", "experience_min", "experience_max",
    "employment_type", "remote", "application_deadline",
}
VALID_TYPES = {"hackathon", "internship", "job"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}

results: list[dict[str, Any]] = []


def validate_item(item: dict, source: str) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in item or not item.get(f):
            errors.append(f"missing required field '{f}'")

    if item.get("type") not in VALID_TYPES and item.get("type"):
        errors.append(f"invalid type '{item['type']}' (expected {VALID_TYPES})")

    if item.get("difficulty") and item["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(f"invalid difficulty '{item['difficulty']}'")

    link = item.get("link", "")
    if link and not link.startswith("http"):
        errors.append(f"link not absolute: {link[:80]}")

    if item.get("prize"):
        prize = item["prize"]
        if len(prize) > 500:
            errors.append(f"prize too long ({len(prize)} chars)")

    if item.get("tags") and len(item["tags"]) > 50:
        errors.append(f"too many tags ({len(item['tags'])} > 50)")

    if item.get("experience_min") is not None and item["experience_min"] < 0:
        errors.append(f"negative experience_min: {item['experience_min']}")

    if item.get("experience_max") is not None and item["experience_max"] < 0:
        errors.append(f"negative experience_max: {item['experience_max']}")

    if item.get("experience_min") is not None and item.get("experience_max") is not None:
        if item["experience_min"] > item["experience_max"]:
            errors.append(f"experience_min > experience_max: {item['experience_min']} > {item['experience_max']}")

    return errors


def run_scraper(source_key: str, timeout_sec: int = 120) -> dict:
    from scrapers import get_scraper_class
    from scrapers.base import SCRAPER_REGISTRY
    config = SCRAPER_REGISTRY.get(source_key)
    if not config:
        return {"source": source_key, "status": "skipped", "reason": "not registered"}

    sc = get_scraper_class(source_key)
    if not sc:
        return {"source": source_key, "status": "skipped", "reason": "no class"}

    if config.requires_api_key:
        return {"source": source_key, "status": "skipped", "reason": "requires API key"}

    start = time.time()
    try:
        scraper = sc()
        items = scraper.run()
        duration = time.time() - start

        all_errors = []
        for i, item in enumerate(items):
            errs = validate_item(item, source_key)
            for e in errs:
                all_errors.append(f"item[{i}]: {e}")

        new_fields_count = sum(1 for item in items for f in ("experience_min", "experience_max", "salary_currency", "employment_type", "remote") if item.get(f))

        return {
            "source": source_key,
            "name": config.name,
            "verticals": config.verticals,
            "status": "success",
            "items": len(items),
            "duration_sec": round(duration, 2),
            "errors": all_errors,
            "error_count": len(all_errors),
            "new_fields_used": new_fields_count,
            "sample": items[:3] if items else [],
            "has_experience_data": any(item.get("experience_min") is not None for item in items),
            "has_remote_data": any(item.get("remote") for item in items),
            "has_salary_currency": any(item.get("salary_currency") for item in items),
        }
    except Exception as exc:
        duration = time.time() - start
        return {
            "source": source_key,
            "name": config.name,
            "verticals": config.verticals,
            "status": "error",
            "items": 0,
            "duration_sec": round(duration, 2),
            "errors": [str(exc)],
            "error_count": 1,
            "sample": [],
        }


def print_report():
    print("=" * 100)
    print(f"SCRAPER VERIFICATION REPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 100)

    summary_by_type = {"hackathon": [], "internship": [], "job": [], "job_lateral": []}

    for r in results:
        for v in r.get("verticals", []):
            if v in summary_by_type:
                summary_by_type[v].append(r)

    for vtype, scrapers in summary_by_type.items():
        if not scrapers:
            continue
        sep = "-" * 40
        print(f"\n{sep} {vtype.upper()} ({len(scrapers)} scrapers) {sep}")
        total_items = sum(r["items"] for r in scrapers)
        total_errors = sum(r["error_count"] for r in scrapers)
        total_duration = sum(r["duration_sec"] for r in scrapers)
        print(f"  Total items: {total_items} | Total errors: {total_errors} | Total duration: {total_duration:.1f}s")

        for r in scrapers:
            status_icon = "[OK]" if r["status"] == "success" else "[SKIP]" if r["status"] == "skipped" else "[FAIL]"
            print(f"\n  {status_icon} {r['name']} ({r['source']})")
            print(f"     Items: {r['items']} | Duration: {r['duration_sec']}s | Errors: {r['error_count']}")
            if r.get("new_fields_used"):
                print(f"     New fields populated: {r['new_fields_used']} occurrences")
                flags = []
                if r.get("has_experience_data"): flags.append("exp")
                if r.get("has_remote_data"): flags.append("remote")
                if r.get("has_salary_currency"): flags.append("currency")
                if flags:
                    print(f"     Flags: {', '.join(flags)}")
            if r["errors"]:
                print(f"     Issues:")
                for e in r["errors"][:5]:
                    print(f"       - {e}")
                if len(r["errors"]) > 5:
                    print(f"       ... and {len(r['errors']) - 5} more")
            if r["sample"]:
                for s in r["sample"]:
                    title = (s.get('title') or '?')[:70]
                    org = (s.get('organizer') or '?')[:30]
                    loc = (s.get('location') or '?')[:25]
                    exp_min = s.get('experience_min', '?')
                    exp_max = s.get('experience_max', '?')
                    remote = s.get('remote', '?')
                    print(f"     -> {title} @ {org} | {loc} | exp={exp_min}-{exp_max} | remote={remote}")

    print(f"\n{'=' * 100}")
    print(f"OVERALL: {len(results)} scrapers | {sum(r['items'] for r in results)} items | {sum(r['error_count'] for r in results)} validation issues")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    sources_to_test = [
        # Hackathons
        "devfolio",
        "devpost",
        "mlh",
        "hackerearth",
        "unstop",
        "dorahacks",
        "techgig",
        "hackerrank",
        "codechef",
        "reskilll",
        # Internships
        "internshala",
        "hellointern",
        "letsintern",
        "twenty19",
        # Jobs (fresher)
        "internshala_jobs",
        "foundit",
        "shine",
        "hirist",
        # Jobs (lateral)
        "cutshort",
        "wellfound",
    ]

    print(f"Testing {len(sources_to_test)} scrapers...\n")

    for src in sources_to_test:
        print(f"  Running {src}...", end=" ")
        sys.stdout.flush()
        r = run_scraper(src, timeout_sec=180)
        results.append(r)
        print(f"{r['status']} ({r['items']} items, {r['error_count']} issues, {r['duration_sec']}s)")

    print_report()
