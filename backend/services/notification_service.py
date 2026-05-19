import logging
from datetime import datetime, timedelta, timezone
from database.supabase_client import db

logger = logging.getLogger(__name__)


def get_upcoming_deadline_opportunities(days: int = 3) -> list[dict]:
    """Get opportunities with deadlines in the next N days."""
    if not db.client:
        return []

    today = datetime.now(timezone.utc).date()
    target = (today + timedelta(days=days)).isoformat()

    result = (
        db.client.table("opportunities")
        .select("id, title, type, deadline")
        .gte("deadline", today.isoformat())
        .lte("deadline", target)
        .eq("is_closed", False)
        .execute()
    )

    return result.data or []


def get_user_notifications(user_id: str) -> list[dict]:
    """Get notifications for a user from the notifications table."""
    if not db.client:
        return []

    # Read from the notifications table (populated by scheduler and API)
    result = (
        db.client.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )

    if result.data:
        return result.data

    # Fallback: generate deadline-based notifications if table is empty
    return _generate_deadline_notifications(user_id)


def _generate_deadline_notifications(user_id: str) -> list[dict]:
    """Generate notifications from upcoming deadlines as fallback."""
    if not db.client:
        return []

    notifications = []

    bookmarks = db.client.table("bookmarks").select("opportunity_id").eq("user_id", user_id).execute()
    applications = db.client.table("applications").select("opportunity_id").eq("user_id", user_id).execute()

    tracked_ids = set()
    for bm in (bookmarks.data or []):
        tracked_ids.add(bm["opportunity_id"])
    for app in (applications.data or []):
        tracked_ids.add(app["opportunity_id"])

    if not tracked_ids:
        return []

    today = datetime.now(timezone.utc).date()
    week_from_now = (today + timedelta(days=7)).isoformat()

    opps = (
        db.client.table("opportunities")
        .select("id, title, deadline")
        .in_("id", list(tracked_ids))
        .gte("deadline", today.isoformat())
        .lte("deadline", week_from_now)
        .execute()
    )

    for opp in (opps.data or []):
        deadline = datetime.fromisoformat(opp["deadline"]).date()
        days_left = (deadline - today).days

        if days_left <= 1:
            urgency = "urgent"
            message = f"Deadline tomorrow: {opp['title']}"
        elif days_left <= 3:
            urgency = "warning"
            message = f"Deadline in {days_left} days: {opp['title']}"
        else:
            urgency = "info"
            message = f"Deadline in {days_left} days: {opp['title']}"

        notifications.append({
            "id": f"deadline-{opp['id']}",
            "type": "deadline",
            "urgency": urgency,
            "title": "Deadline Reminder",
            "message": message,
            "opportunity_id": opp["id"],
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    return notifications
