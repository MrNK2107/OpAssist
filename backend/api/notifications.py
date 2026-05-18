from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from database.supabase_client import db
from api.deps import get_current_user_id
from services.notification_service import get_user_notifications

router = APIRouter()


@router.get("")
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, le=100),
    unread_only: bool = Query(False),
) -> dict:
    """Get user's notifications with deadline fallback."""
    if not db.client:
        return {"data": [], "unread_count": 0}

    all_notifications = get_user_notifications(user_id)

    # Compute unread count from full set
    unread_count = sum(1 for n in all_notifications if not n.get("is_read", False))

    # Apply unread filter
    notifications = all_notifications
    if unread_only:
        notifications = [n for n in notifications if not n.get("is_read", False)]

    # Apply limit
    notifications = notifications[:limit]

    return {
        "data": notifications,
        "unread_count": unread_count,
    }


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Mark a notification as read."""
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    result = (
        db.client.table("notifications")
        .update({"is_read": True})
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification marked as read"}


@router.put("/read-all")
async def mark_all_notifications_read(
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Mark all notifications as read."""
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    db.client.table("notifications").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()

    return {"message": "All notifications marked as read"}
