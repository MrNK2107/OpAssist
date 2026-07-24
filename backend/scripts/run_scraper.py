#!/usr/bin/env python
"""Run all scrapers from the command line.

Usage:
    python scripts/run_scraper.py            # Run all scrapers
    python scripts/run_scraper.py --source devfolio  # Run a single source
    python scripts/run_scraper.py --list     # List available sources
"""

import sys
import time
import argparse
from pathlib import Path

# Ensure the backend directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def list_sources():
    """Print available scraper sources from the registry."""
    from scrapers import SCRAPER_REGISTRY

    sources = [
        (k, ", ".join(v.verticals), v.description)
        for k, v in SCRAPER_REGISTRY.items()
    ]
    print("Available scraper sources:")
    for name, kinds, desc in sources:
        print(f"  {name:20s}  ({kinds:35s}) {desc}")

    print(f"\nTotal: {len(sources)} sources")


def run_all():
    """Run all scrapers via the scraper service."""
    from services.scraper_service import run_full_scrape

    print("Starting full scrape...")
    start = time.time()
    result = run_full_scrape()
    elapsed = time.time() - start

    print(f"\nScrape completed in {elapsed:.1f}s")
    print(f"Expired entries deleted: {result.get('expired_deleted', 0)}")
    print(f"Duplicates removed: {result.get('duplicates_removed', 0)}")
    print()

    sources = result.get("sources", {})
    for name, info in sources.items():
        status = info.get("status", "?")
        items = info.get("items_found", 0)
        new = info.get("items_new", 0)
        updated = info.get("items_updated", 0)
        err = info.get("errors", 0)
        icon = "✓" if status == "success" else "✗"
        extra = ""
        if err:
            extra = f" ({err} errors)"
        print(f"  {icon} {name:20s}  {items:3d} found  {new:3d} new  {updated:3d} updated{extra}")


def run_single(source: str):
    """Run a single scraper source by key (uses registry)."""
    from services.scraper_service import run_scraper, upsert_opportunities
    from scrapers import SCRAPER_REGISTRY

    if source not in SCRAPER_REGISTRY:
        print(f"Unknown source: {source}")
        print("Use --list to see available sources.")
        sys.exit(1)

    print(f"Running scraper: {source}...")
    start = time.time()
    items, error = run_scraper(source)
    elapsed = time.time() - start

    if error:
        print(f"  ✗ Failed: {error}")
    else:
        stats = upsert_opportunities(items, source)
        print(f"  ✓ {len(items)} items found in {elapsed:.1f}s")
        print(f"    {stats['new']} new, {stats['updated']} updated, {stats['errors']} errors")


def main():
    parser = argparse.ArgumentParser(description="OpAssist scraper CLI")
    parser.add_argument("--source", "-s", help="Run a single scraper source by name")
    parser.add_argument("--list", "-l", action="store_true", help="List available sources")
    args = parser.parse_args()

    if args.list:
        list_sources()
    elif args.source:
        run_single(args.source)
    else:
        run_all()


if __name__ == "__main__":
    main()
