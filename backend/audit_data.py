"""Data quality audit for scrapers that work."""

import logging
logging.basicConfig(level=logging.WARNING)

from scrapers import get_scraper_class
from scrapers.base import SCRAPER_REGISTRY

SOURCES = ["devpost", "unstop", "internshala", "internshala_jobs", "foundit"]

for src in SOURCES:
    sc = get_scraper_class(src)
    cfg = SCRAPER_REGISTRY.get(src)
    print(f"\n{'='*70}")
    print(f"  {cfg.name} ({src})")
    print(f"{'='*70}")

    try:
        items = sc().run()
        print(f"  Total items: {len(items)}")

        # New fields stats
        exp_ct = sum(1 for i in items if i.get("experience_min") is not None)
        exp_max_ct = sum(1 for i in items if i.get("experience_max") is not None)
        remote_ct = sum(1 for i in items if i.get("remote"))
        emp_ct = sum(1 for i in items if i.get("employment_type"))
        cur_ct = sum(1 for i in items if i.get("salary_currency"))
        print(f"  Lateral fields: experience_min={exp_ct}, experience_max={exp_max_ct}, remote={remote_ct}, emp_type={emp_ct}, currency={cur_ct}")

        # Validate
        bad_link = sum(1 for i in items if not i.get("link") or not i["link"].startswith("http"))
        no_title = sum(1 for i in items if not i.get("title"))
        bad_type = sum(1 for i in items if i.get("type") not in ("hackathon", "internship", "job"))
        print(f"  Validation: bad_link={bad_link}, no_title={no_title}, bad_type={bad_type}")

        # Field coverage
        fields = set()
        for i in items:
            fields.update(k for k, v in i.items() if v is not None and v != "" and v != [])
        print(f"  Fields populated: {sorted(fields)}")

        # Sample
        print(f"  Samples:")
        for s in items[:3]:
            print(f"    Title:      {s.get('title', '?')[:70]}")
            print(f"    Organizer:  {s.get('organizer', '?')[:40]}")
            print(f"    Location:   {s.get('location', '?')[:30]}")
            print(f"    Prize:      {s.get('prize', '?')[:50]}")
            print(f"    Exp range:  {s.get('experience_min', 'N/A')} - {s.get('experience_max', 'N/A')}")
            print(f"    Remote:     {s.get('remote', 'N/A')}")
            print(f"    Emp type:   {s.get('employment_type', 'N/A')}")
            print(f"    Currency:   {s.get('salary_currency', 'N/A')}")
            print()

    except Exception as e:
        print(f"  FAILED: {e}")
