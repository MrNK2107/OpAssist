import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from scrapers import SCRAPER_REGISTRY, get_all_source_keys

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(scrape_interval_hours: int = 6):
    from services.scraper_service import (
        run_full_scrape, run_scrape_for_vertical,
        delete_expired, deduplicate_opportunities,
    )

    # Full scrape at the configured interval
    scheduler.add_job(
        run_full_scrape,
        trigger=IntervalTrigger(hours=scrape_interval_hours),
        id="full_scrape",
        name="Full scrape of all sources",
        replace_existing=True,
    )

    # Staggered per-vertical scraping
    # Jobs and internships scrape more frequently
    scheduler.add_job(
        lambda: run_scrape_for_vertical("job"),
        trigger=IntervalTrigger(hours=4),
        id="scrape_jobs",
        name="Jobs scrape (every 4h)",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_scrape_for_vertical("job_lateral"),
        trigger=IntervalTrigger(hours=6),
        id="scrape_jobs_lateral",
        name="Lateral/experienced jobs scrape (every 6h)",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_scrape_for_vertical("internship"),
        trigger=IntervalTrigger(hours=4),
        id="scrape_internships",
        name="Internships scrape (every 4h)",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: run_scrape_for_vertical("hackathon"),
        trigger=IntervalTrigger(hours=8),
        id="scrape_hackathons",
        name="Hackathons scrape (every 8h)",
        replace_existing=True,
    )

    # Hourly expired cleanup
    scheduler.add_job(
        delete_expired,
        trigger=IntervalTrigger(hours=1),
        id="delete_expired",
        name="Delete expired opportunities",
        replace_existing=True,
    )

    # Deduplicate every 6 hours
    scheduler.add_job(
        deduplicate_opportunities,
        trigger=IntervalTrigger(hours=6),
        id="deduplicate",
        name="Deduplicate opportunities",
        replace_existing=True,
    )

    # Daily deadline check at 9 AM
    scheduler.add_job(
        check_deadlines,
        trigger=CronTrigger(hour=9, minute=0),
        id="deadline_check",
        name="Check upcoming deadlines",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started — full scrape every {scrape_interval_hours}h, "
        f"jobs every 4h, lateral jobs every 6h, internships every 4h, "
        f"hackathons every 8h, expired cleanup every 1h, "
        f"dedup every 6h, deadline check at 9 AM"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


async def check_deadlines():
    from database.supabase_client import db
    from datetime import datetime, timedelta, timezone

    if not db.client:
        return

    try:
        today = datetime.now(timezone.utc).date()
        three_days = (today + timedelta(days=3)).isoformat()

        result = (
            db.client.table("opportunities")
            .select("id, title, deadline")
            .gte("deadline", today.isoformat())
            .lte("deadline", three_days)
            .eq("is_closed", False)
            .execute()
        )

        if not result.data:
            return

        logger.info(f"Found {len(result.data)} opportunities with deadlines in 3 days")

        for opp in result.data:
            opp_id = opp["id"]
            deadline = opp["deadline"]
            title = opp["title"]

            deadline_date = datetime.fromisoformat(deadline).date() if deadline else None
            if not deadline_date:
                continue
            days_left = (deadline_date - today).days

            if days_left <= 1:
                urgency = "urgent"
                notif_title = "Deadline Tomorrow"
                message = f"Deadline tomorrow: {title}"
            elif days_left <= 3:
                urgency = "warning"
                notif_title = "Deadline Soon"
                message = f"Deadline in {days_left} days: {title}"
            else:
                continue

            bookmarks = db.client.table("bookmarks").select("user_id").eq("opportunity_id", opp_id).execute()
            applications = db.client.table("applications").select("user_id").eq("opportunity_id", opp_id).execute()

            user_ids = set()
            for bm in (bookmarks.data or []):
                user_ids.add(bm["user_id"])
            for app in (applications.data or []):
                user_ids.add(app["user_id"])

            for uid in user_ids:
                existing = (
                    db.client.table("notifications")
                    .select("id")
                    .eq("user_id", uid)
                    .eq("opportunity_id", opp_id)
                    .eq("type", "deadline")
                    .gte("created_at", today.isoformat())
                    .execute()
                )

                if not existing.data:
                    db.client.table("notifications").insert({
                        "user_id": uid,
                        "type": "deadline",
                        "urgency": urgency,
                        "title": notif_title,
                        "message": message,
                        "opportunity_id": opp_id,
                    }).execute()

        logger.info("Deadline notifications created successfully")

    except Exception as exc:
        logger.error(f"Deadline check failed: {exc}")
