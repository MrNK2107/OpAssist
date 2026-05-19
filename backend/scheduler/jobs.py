import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(scrape_interval_hours: int = 6):
    """Start the background scheduler."""
    from services.scraper_service import run_full_scrape, delete_expired

    # Periodic scraping
    scheduler.add_job(
        run_full_scrape,
        trigger=IntervalTrigger(hours=scrape_interval_hours),
        id="full_scrape",
        name="Full scrape of all sources",
        replace_existing=True,
    )

    # Hourly expired-entry cleanup
    scheduler.add_job(
        delete_expired,
        trigger=IntervalTrigger(hours=1),
        id="delete_expired",
        name="Delete expired opportunities",
        replace_existing=True,
    )

    # Daily deadline check (runs at 9 AM)
    scheduler.add_job(
        check_deadlines,
        trigger=CronTrigger(hour=9, minute=0),
        id="deadline_check",
        name="Check upcoming deadlines",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started — scraping every {scrape_interval_hours}h, expired cleanup every 1h, deadline check at 9 AM")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


async def check_deadlines():
    """Check for upcoming deadlines and create notification records."""
    from database.supabase_client import db
    from datetime import datetime, timedelta, timezone

    if not db.client:
        return

    try:
        # Get opportunities with deadlines in the next 3 days
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

        # For each opportunity, find users who bookmarked or applied
        for opp in result.data:
            opp_id = opp["id"]
            deadline = opp["deadline"]
            title = opp["title"]

            # Calculate days left
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
                continue  # Skip if more than 3 days away

            # Find users who bookmarked this opportunity
            bookmarks = db.client.table("bookmarks").select("user_id").eq("opportunity_id", opp_id).execute()
            # Find users who applied to this opportunity
            applications = db.client.table("applications").select("user_id").eq("opportunity_id", opp_id).execute()

            # Collect unique user IDs
            user_ids = set()
            for bm in (bookmarks.data or []):
                user_ids.add(bm["user_id"])
            for app in (applications.data or []):
                user_ids.add(app["user_id"])

            # Create notifications for each user (skip if already exists today)
            for uid in user_ids:
                # Check if notification already exists for this opportunity today
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
