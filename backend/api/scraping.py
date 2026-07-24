from fastapi import APIRouter, BackgroundTasks, Depends, Query
from database.supabase_client import db
from config import get_settings
from api.deps import get_current_user_id
from scrapers import SCRAPER_REGISTRY, get_all_source_keys, get_scrapers_for_vertical
from services.scraper_health import health_tracker

settings = get_settings()
router = APIRouter()


@router.post("/trigger")
async def trigger_scrape() -> dict:
    from services.scraper_service import run_full_scrape
    try:
        result = run_full_scrape()
        return {"message": "Scrape completed", "status": "done", "result": result}
    except Exception as exc:
        return {"message": "Scrape failed", "status": "error", "error": str(exc)}


@router.post("/trigger/{vertical}")
async def trigger_vertical_scrape(vertical: str) -> dict:
    from services.scraper_service import run_scrape_for_vertical
    if vertical not in ("hackathon", "internship", "job"):
        return {"message": f"Invalid vertical: {vertical}", "status": "error"}
    result = run_scrape_for_vertical(vertical)
    return {"message": f"Scrape completed for {vertical}", "status": "done", "result": result}


@router.get("/status")
async def get_scrape_status() -> dict:
    from services.scraper_service import get_last_scrape_info
    from scheduler.jobs import scheduler

    if not db.client:
        return {"status": "idle", "last_run": None, "next_run": None, "sources": {}}

    result = db.client.table("opportunities").select("source").execute()
    sources: dict[str, int] = {}
    for row in (result.data or []):
        src = row.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    scrape_info = get_last_scrape_info()
    next_run = None
    try:
        job = scheduler.get_job("full_scrape")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    except Exception:
        pass

    return {
        "status": "idle",
        "last_run": scrape_info.get("last_run"),
        "last_duration": scrape_info.get("duration_seconds"),
        "next_run": next_run,
        "sources": {src: {"status": "success", "items": count} for src, count in sources.items()},
    }


@router.get("/health")
async def get_scraper_health() -> dict:
    return {
        "summary": health_tracker.summary(),
        "sources": health_tracker.get_all_stats(),
        "registry": {
            k: {
                "name": v.name,
                "verticals": v.verticals,
                "priority": v.priority,
                "status": v.status,
                "requires_playwright": v.requires_playwright,
            }
            for k, v in SCRAPER_REGISTRY.items()
        },
    }


@router.post("/source/{source}/toggle")
async def toggle_source(
    source: str,
    enabled: bool = Query(True),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    if source not in SCRAPER_REGISTRY:
        return {"message": f"Unknown source: {source}", "source": source, "enabled": False}

    if not db.client:
        return {"message": f"Source {source} {'enabled' if enabled else 'disabled'}", "source": source, "enabled": enabled}

    db.client.table("scraper_config").upsert({"source": source, "enabled": enabled}, on_conflict="source").execute()
    return {"message": f"Source {source} {'enabled' if enabled else 'disabled'}", "source": source, "enabled": enabled}


@router.get("/sources")
async def get_sources() -> dict:
    sources = []
    for source_key in get_all_source_keys():
        config = SCRAPER_REGISTRY[source_key]
        sources.append({
            "name": source_key,
            "label": config.name,
            "type": ",".join(config.verticals),
            "priority": config.priority,
            "status": config.status,
            "requires_playwright": config.requires_playwright,
            "requires_api_key": config.requires_api_key,
            "interval_hours": config.interval_hours,
            "description": config.description,
        })

    return {
        "sources": sorted(sources, key=lambda s: (s["status"] != "active", s["priority"] != "critical")),
        "total": len(sources),
        "by_vertical": {
            "hackathon": len(get_scrapers_for_vertical("hackathon")),
            "internship": len(get_scrapers_for_vertical("internship")),
            "job": len(get_scrapers_for_vertical("job")),
        },
    }
