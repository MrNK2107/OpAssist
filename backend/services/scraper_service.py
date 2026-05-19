import logging
import time
from datetime import datetime, timezone
from database.supabase_client import db

logger = logging.getLogger(__name__)

# Module-level state for scrape status tracking
_last_run_time: str | None = None
_last_run_results: dict | None = None
_last_run_duration: float | None = None


def run_scraper(scraper_class, **kwargs):
    """Run a single scraper."""
    try:
        scraper = scraper_class(**kwargs)
        results = scraper.run()
        return results, None
    except Exception as exc:
        logger.error(f"Scraper {scraper_class.__name__} failed: {exc}", exc_info=True)
        return [], str(exc)


def delete_expired() -> int:
    """Delete opportunities whose deadline has passed. Returns count of deleted rows."""
    if not db.client:
        logger.warning("No database client — skipping expired cleanup")
        return 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        # Fetch expired entries to count them
        result = (
            db.client.table("opportunities")
            .select("id", count="exact")
            .not_.is_("deadline", "null")
            .lt("deadline", today)
            .execute()
        )
        count = result.count or 0
        if count == 0:
            return 0

        # Delete them
        db.client.table("opportunities").delete().not_.is_("deadline", "null").lt("deadline", today).execute()
        logger.info(f"Deleted {count} expired opportunities")
        return count
    except Exception as exc:
        logger.error(f"Failed to delete expired opportunities: {exc}", exc_info=True)
        return 0


def deduplicate_opportunities() -> int:
    """Remove duplicate opportunities with same title+organizer but different URLs.
    Keeps the entry with the most data (longest description, has deadline, etc.)."""
    if not db.client:
        return 0

    try:
        result = db.client.table("opportunities").select("id, title, organizer, url, source, deadline, description").execute()
        if not result.data:
            return 0

        # Group by normalized (title, organizer)
        from collections import defaultdict
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for row in result.data:
            key = (row["title"].strip().lower(), row["organizer"].strip().lower())
            if key[0]:  # skip empty titles
                groups[key].append(row)

        deleted = 0
        for key, rows in groups.items():
            if len(rows) <= 1:
                continue
            # Score each row: prefer longer description, has deadline, has image_url
            def score(r):
                s = len(r.get("description") or "")
                s += 100 if r.get("deadline") else 0
                s += 10 if r.get("url") else 0
                return s
            rows.sort(key=score, reverse=True)
            # Delete all but the best one
            for row in rows[1:]:
                try:
                    db.client.table("opportunities").delete().eq("id", row["id"]).execute()
                    deleted += 1
                except Exception:
                    pass

        if deleted:
            logger.info(f"Deduplicated {deleted} opportunities")
        return deleted
    except Exception as exc:
        logger.error(f"Failed to deduplicate: {exc}", exc_info=True)
        return 0


def upsert_opportunities(items: list[dict], source: str) -> dict:
    """Upsert scraped items into the database."""
    if not db.client:
        logger.warning("No database client — skipping upsert")
        return {"new": 0, "updated": 0, "errors": 0}

    new = 0
    updated = 0
    errors = 0

    for item in items:
        try:
            data = {
                "title": item.get("title", ""),
                "type": item.get("type", "hackathon"),
                "url": item.get("link", ""),
                "source": source,
                "description": item.get("description", ""),
                "organizer": item.get("organizer", ""),
                "start_date": item.get("start_date") or None,
                "end_date": item.get("end_date") or None,
                "deadline": item.get("date") or item.get("deadline") or None,
                "location": item.get("location", ""),
                "prize": item.get("prize", ""),
                "tags": item.get("tags", []),
                "difficulty": item.get("difficulty", "beginner"),
                "is_closed": item.get("is_closed", False),
                "image_url": item.get("image_url", ""),
            }

            # H1: Skip items with empty URLs to prevent data collision
            url = data.get("url")
            if not url:
                logger.debug(f"Skipping item with empty URL: {data.get('title')}")
                errors += 1
                continue

            # H5: Preserve date/image fields if None, but clear other fields
            PRESERVE_IF_NONE = {"start_date", "end_date", "deadline", "image_url"}
            data = {k: v for k, v in data.items() if v is not None or k not in PRESERVE_IF_NONE}

            # L1: Upsert directly (no pre-check SELECT — atomic operation)
            result = db.upsert_opportunity(data)
            if result.data:
                new += 1  # Supabase doesn't distinguish insert vs update in result
        except Exception as exc:
            logger.error(f"Failed to upsert opportunity: {exc}")
            errors += 1

    return {"new": new, "updated": updated, "errors": errors}


def get_last_scrape_info() -> dict:
    """Get info about the last scrape run."""
    return {
        "last_run": _last_run_time,
        "duration_seconds": _last_run_duration,
        "results": _last_run_results,
    }


def run_full_scrape() -> dict:
    """Run all scrapers and upsert results."""
    global _last_run_time, _last_run_results, _last_run_duration

    from scrapers.devfolio import DevfolioScraper
    from scrapers.unstop import UnstopScraper
    from scrapers.hackerearth import HackerEarthScraper
    from scrapers.github_oss import GitHubOSSScraper
    from scrapers.devpost import DevpostScraper
    from scrapers.hack2skill import Hack2SkillScraper
    from scrapers.mlh import MLHScraper
    from scrapers.internshala import InternshalaScraper

    scrapers = [
        (DevfolioScraper, "devfolio"),
        (UnstopScraper, "unstop"),
        (HackerEarthScraper, "hackerearth"),
        (GitHubOSSScraper, "github"),
        (DevpostScraper, "devpost"),
        (Hack2SkillScraper, "hack2skill"),
        (MLHScraper, "mlh"),
        (InternshalaScraper, "internshala"),
    ]

    results = {}
    start_time = time.time()

    for scraper_class, source in scrapers:
        logger.info(f"Running scraper: {source}")
        items, error = run_scraper(scraper_class)

        if error:
            results[source] = {"status": "error", "error": error, "items": 0}
            continue

        stats = upsert_opportunities(items, source)
        results[source] = {
            "status": "success",
            "items_found": len(items),
            "items_new": stats["new"],
            "items_updated": stats["updated"],
            "errors": stats["errors"],
        }

    # M8: Deduplicate by title+organizer
    deduped = deduplicate_opportunities()

    # Clean up expired opportunities
    expired_deleted = delete_expired()

    duration = time.time() - start_time
    timestamp = datetime.now(timezone.utc).isoformat()

    # Update module-level state
    _last_run_time = timestamp
    _last_run_duration = round(duration, 1)
    _last_run_results = results

    logger.info(f"Full scrape completed in {duration:.1f}s: {results}")

    return {
        "duration_seconds": round(duration, 1),
        "sources": results,
        "duplicates_removed": deduped,
        "expired_deleted": expired_deleted,
        "timestamp": timestamp,
    }
