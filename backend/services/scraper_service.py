import logging
import time
from datetime import datetime, timezone
from typing import Optional
from database.supabase_client import db
from scrapers import (
    get_scraper_class, get_all_source_keys, get_scrapers_for_vertical,
    SCRAPER_REGISTRY, SourceConfig, GenericScraper,
)
from services.scraper_health import health_tracker
from models.schemas import OpportunityType

logger = logging.getLogger(__name__)

_last_run_time: Optional[str] = None
_last_run_results: Optional[dict] = None
_last_run_duration: Optional[float] = None


VALID_OPPORTUNITY_TYPES = {item.value for item in OpportunityType}
TYPE_ALIASES = {
    "fellowship": "event",
    "job_lateral": "job",
}


def normalize_opportunity_type(value: str | None) -> str:
    candidate = (value or "hackathon").strip().lower()
    candidate = TYPE_ALIASES.get(candidate, candidate)
    if candidate not in VALID_OPPORTUNITY_TYPES:
        return "hackathon"
    return candidate


def run_scraper(source_key: str | type[GenericScraper]) -> tuple[list[dict], Optional[str]]:
    config = None
    source_name = getattr(source_key, "__name__", str(source_key))
    if isinstance(source_key, str):
        source_name = source_key
        config = SCRAPER_REGISTRY.get(source_key)
        if not config:
            return [], f"Unknown source: {source_key}"
        scraper_class = get_scraper_class(source_key)
        if not scraper_class:
            return [], f"No scraper class for {source_key}"
    else:
        scraper_class = source_key
    start = time.time()
    try:
        scraper = scraper_class()
        results = scraper.run()
        duration = time.time() - start
        health_tracker.record_run(source_name, len(results), duration)
        if config:
            health_tracker.set_source_status(source_name, config.status)
        return results, None
    except Exception as exc:
        duration = time.time() - start
        err_msg = str(exc)
        health_tracker.record_run(source_name, 0, duration, error=err_msg)
        health_tracker.set_source_status(source_name, "unstable")
        logger.error(f"Scraper {source_name} failed: {exc}", exc_info=True)
        return [], err_msg


def delete_expired() -> int:
    if not db.client:
        logger.warning("No database client — skipping expired cleanup")
        return 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
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
        db.client.table("opportunities").delete().not_.is_("deadline", "null").lt("deadline", today).execute()
        logger.info(f"Deleted {count} expired opportunities")
        return count
    except Exception as exc:
        logger.error(f"Failed to delete expired opportunities: {exc}", exc_info=True)
        return 0


def deduplicate_opportunities() -> int:
    if not db.client:
        return 0
    try:
        result = db.client.table("opportunities").select("id, title, organizer, url, source, deadline, description, experience_min, experience_max").execute()
        if not result.data:
            return 0
        from collections import defaultdict
        groups: dict[tuple, list[dict]] = defaultdict(list)
        for row in result.data:
            key = (
                row["title"].strip().lower() if row["title"] else "",
                row["organizer"].strip().lower() if row["organizer"] else "",
                row.get("experience_min"),
                row.get("experience_max"),
            )
            if key[0]:
                groups[key].append(row)
        deleted = 0
        for key, rows in groups.items():
            if len(rows) <= 1:
                continue
            def score(r):
                s = len(r.get("description") or "")
                s += 100 if r.get("deadline") else 0
                s += 10 if r.get("url") else 0
                return s
            rows.sort(key=score, reverse=True)
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
                "type": normalize_opportunity_type(item.get("type")),
                "url": item.get("link", ""),
                "source": source,
                "description": item.get("description", ""),
                "organizer": item.get("organizer", ""),
                "start_date": item.get("start_date") or None,
                "end_date": item.get("end_date") or None,
                "deadline": item.get("date") or item.get("deadline") or None,
                "location": item.get("location", ""),
                "prize": item.get("prize", ""),
                "salary_currency": item.get("salary_currency", "INR"),
                "experience_min": item.get("experience_min"),
                "experience_max": item.get("experience_max"),
                "employment_type": item.get("employment_type"),
                "remote": item.get("remote", False),
                "application_deadline": item.get("application_deadline"),
                "tags": item.get("tags", []),
                "difficulty": item.get("difficulty", "beginner"),
                "is_closed": item.get("is_closed", False),
                "image_url": item.get("image_url", ""),
            }
            url = data.get("url")
            if not url:
                logger.debug(f"Skipping item with empty URL: {data.get('title')}")
                errors += 1
                continue
            PRESERVE_IF_NONE = {"start_date", "end_date", "deadline", "image_url", "experience_min", "experience_max", "application_deadline"}
            data = {k: v for k, v in data.items() if v is not None or k not in PRESERVE_IF_NONE}
            result = db.upsert_opportunity(data)
            if result.data:
                new += 1
        except Exception as exc:
            logger.error(f"Failed to upsert opportunity: {exc}")
            errors += 1
    return {"new": new, "updated": updated, "errors": errors}


def get_last_scrape_info() -> dict:
    return {
        "last_run": _last_run_time,
        "duration_seconds": _last_run_duration,
        "results": _last_run_results,
    }


def run_scrape_for_vertical(vertical: str) -> dict:
    logger.info(f"Running scrape for vertical: {vertical}")
    sources = get_scrapers_for_vertical(vertical)
    results = {}
    for source_key, config in sources:
        if config.status == "broken":
            logger.info(f"Skipping broken scraper: {source_key}")
            continue
        logger.info(f"Running scraper: {source_key}")
        items, error = run_scraper(source_key)
        if error:
            results[source_key] = {"status": "error", "error": error, "items": 0}
            continue
        stats = upsert_opportunities(items, source_key)
        health_tracker.record_upsert_errors(source_key, stats["errors"])
        results[source_key] = {
            "status": "success",
            "items_found": len(items),
            "items_new": stats["new"],
            "items_updated": stats["updated"],
            "errors": stats["errors"],
        }
    return results


def run_full_scrape() -> dict:
    global _last_run_time, _last_run_results, _last_run_duration
    results = {}
    start_time = time.time()

    for source_key in get_all_source_keys():
        config = SCRAPER_REGISTRY.get(source_key)
        if config and config.status == "broken":
            logger.info(f"Skipping broken scraper: {source_key}")
            continue
        logger.info(f"Running scraper: {source_key}")
        items, error = run_scraper(source_key)
        if error:
            results[source_key] = {"status": "error", "error": error, "items": 0}
            continue
        stats = upsert_opportunities(items, source_key)
        results[source_key] = {
            "status": "success",
            "items_found": len(items),
            "items_new": stats["new"],
            "items_updated": stats["updated"],
            "errors": stats["errors"],
        }

    deduped = deduplicate_opportunities()
    expired_deleted = delete_expired()
    duration = time.time() - start_time
    timestamp = datetime.now(timezone.utc).isoformat()

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
