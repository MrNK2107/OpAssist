from fastapi import APIRouter, BackgroundTasks, Depends, Query
from database.supabase_client import db
from config import get_settings
from api.deps import get_current_user_id

settings = get_settings()
router = APIRouter()


@router.post("/trigger")
async def trigger_scrape() -> dict:
    """Trigger manual scrape."""
    from services.scraper_service import run_full_scrape

    try:
        result = run_full_scrape()
        return {
            "message": "Scrape completed",
            "status": "done",
            "result": result,
        }
    except Exception as exc:
        return {
            "message": "Scrape failed",
            "status": "error",
            "error": str(exc),
        }


@router.get("/status")
async def get_scrape_status() -> dict:
    """Get scrape status — counts by source from DB."""
    from services.scraper_service import get_last_scrape_info
    from scheduler.jobs import scheduler

    if not db.client:
        return {"status": "idle", "last_run": None, "next_run": None, "sources": {}}

    result = db.client.table("opportunities").select("source").execute()
    sources: dict[str, int] = {}
    for row in (result.data or []):
        src = row.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    # Get last run info from scraper service
    scrape_info = get_last_scrape_info()

    # Get next run time from scheduler
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


@router.post("/source/{source}/toggle")
async def toggle_source(
    source: str,
    enabled: bool = Query(True),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Enable/disable a scraper source."""
    if not db.client:
        return {"message": f"Source {source} {'enabled' if enabled else 'disabled'}", "source": source, "enabled": enabled}

    result = (
        db.client.table("scraper_config")
        .upsert({"source": source, "enabled": enabled}, on_conflict="source")
        .execute()
    )

    return {
        "message": f"Source {source} {'enabled' if enabled else 'disabled'}",
        "source": source,
        "enabled": enabled,
    }


@router.get("/sources")
async def get_sources() -> dict:
    """Get available scraper sources from config table."""
    if not db.client:
        return {
            "sources": [
                {"name": "devfolio", "enabled": True, "type": "hackathon"},
                {"name": "unstop", "enabled": True, "type": "hackathon,internship,scholarship"},
                {"name": "hackerearth", "enabled": True, "type": "challenge,hackathon"},
                {"name": "github", "enabled": True, "type": "oss,gsoc"},
                {"name": "devpost", "enabled": True, "type": "hackathon"},
                {"name": "hack2skill", "enabled": True, "type": "hackathon"},
                {"name": "mlh", "enabled": True, "type": "hackathon"},
                {"name": "internshala", "enabled": True, "type": "internship"},
            ]
        }

    result = db.client.table("scraper_config").select("*").execute()

    source_types = {
        "devfolio": "hackathon",
        "unstop": "hackathon,internship,scholarship",
        "hackerearth": "challenge,hackathon",
        "github": "oss,gsoc",
        "devpost": "hackathon",
        "hack2skill": "hackathon",
        "mlh": "hackathon",
        "internshala": "internship",
    }

    sources = []
    for row in (result.data or []):
        sources.append({
            "name": row["source"],
            "enabled": row["enabled"],
            "type": source_types.get(row["source"], "other"),
            "last_run": row.get("last_run"),
        })

    return {"sources": sources}
