"""Quick verification of scrapers that produced data + testing new lateral scrapers."""

import json
import logging
import sys
import time
from datetime import datetime, timezone

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(name)s | %(message)s")


def check_scraper(source_key: str):
    from scrapers import get_scraper_class
    from scrapers.base import SCRAPER_REGISTRY

    config = SCRAPER_REGISTRY.get(source_key)
    sc = get_scraper_class(source_key)
    if not sc or not config:
        return {"source": source_key, "status": "SKIP", "items": 0, "errors": [], "sample": []}

    if config.requires_api_key:
        return {"source": source_key, "status": "SKIP (api key)", "items": 0, "errors": [], "sample": []}

    start = time.time()
    try:
        scraper = sc()
        items = scraper.run()
        dur = round(time.time() - start, 2)

        issues = []
        for i, item in enumerate(items):
            if not item.get("title"): issues.append(f"item[{i}]: no title")
            if not item.get("link"): issues.append(f"item[{i}]: no link")
            if item.get("link") and not item["link"].startswith("http"): issues.append(f"item[{i}]: bad link")
            if item.get("experience_min") is not None and item["experience_max"] is not None:
                if item["experience_min"] > item["experience_max"]:
                    issues.append(f"item[{i}]: exp_min > exp_max ({item['experience_min']}>{item['experience_max']})")

        lateral_fields_used = sum(1 for it in items for f in ("experience_min","experience_max","salary_currency","employment_type","remote") if it.get(f))

        return {
            "source": source_key,
            "name": config.name,
            "status": "OK",
            "items": len(items),
            "duration": dur,
            "errors": issues,
            "lateral_fields": lateral_fields_used,
            "sample": items[:5],
        }
    except Exception as e:
        dur = round(time.time() - start, 2)
        return {"source": source_key, "name": config.name, "status": f"FAIL: {e}", "items": 0, "duration": dur, "errors": [str(e)], "lateral_fields": 0, "sample": []}


results = []
sources = [
    # Hackathons that worked
    "devpost", "dorahacks", "unstop", "hackerrank", "codechef",
    # Internships
    "internshala", "hellointern",
    # Jobs
    "internshala_jobs", "foundit", "shine",
    # Lateral
    "cutshort", "wellfound",
]

print(f"Running {len(sources)} scrapers...\n")
for src in sources:
    print(f"  {src}...", end=" ", flush=True)
    r = check_scraper(src)
    results.append(r)
    print(f"{r['status']} ({r['items']} items, {r['duration']}s)")

print(f"\n{'='*90}")
print(f"RESULTS SUMMARY")
print(f"{'='*90}")

for r in results:
    print(f"\n[{r['status']}] {r['name']} ({r['source']})")
    print(f"  Items: {r['items']} | Duration: {r['duration']}s")
    if r['lateral_fields']:
        print(f"  New lateral fields populated: {r['lateral_fields']} occurrences")
    if r['errors']:
        for e in r['errors'][:5]:
            print(f"  ERROR: {e}")
    for s in r.get('sample', []):
        exp_info = ""
        if s.get('experience_min') is not None or s.get('experience_max') is not None:
            exp_info = f" exp={s.get('experience_min','?')}-{s.get('experience_max','?')}"
        remote_info = " [REMOTE]" if s.get('remote') else ""
        emp_info = f" [{s.get('employment_type','')}]" if s.get('employment_type') else ""
        title = (s.get('title') or '?')[:60]
        org = (s.get('organizer') or '?')[:25]
        loc = (s.get('location') or '?')[:20]
        print(f"    -> {title} @ {org} | {loc}{exp_info}{remote_info}{emp_info}")

print(f"\n{'='*90}")

# Detailed data quality audit for successful scrapers
print(f"\n{'='*90}")
print(f"DETAILED DATA QUALITY AUDIT")
print(f"{'='*90}")

for r in results:
    if r['status'] != 'OK' or not r['sample']:
        continue
    print(f"\n--- {r['name']} ({r['source']}) ---")
    for i, s in enumerate(r['sample']):
        print(f"  Item {i+1}:")
        print(f"    Title:       {s.get('title','?')}")
        print(f"    Organizer:   {s.get('organizer','?')}")
        print(f"    Location:    {s.get('location','?')}")
        print(f"    Type:        {s.get('type','?')}")
        print(f"    Prize:       {s.get('prize','?')}")
        print(f"    Link:        {(s.get('link') or '?')[:80]}")
        print(f"    Difficulty:  {s.get('difficulty','?')}")
        print(f"    Tags:        {s.get('tags',[])[:5]}")
        print(f"    Exp Range:   {s.get('experience_min','N/A')} - {s.get('experience_max','N/A')}")
        print(f"    Remote:      {s.get('remote','N/A')}")
        print(f"    Emp Type:    {s.get('employment_type','N/A')}")
        print(f"    Currency:    {s.get('salary_currency','N/A')}")
        print(f"    Deadline:    {s.get('date','N/A')}")
        print()
