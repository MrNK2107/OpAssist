from fastapi import APIRouter, HTTPException, Depends
from models.schemas import Application, ApplicationUpdate, ApplicationEvent
from database.supabase_client import db
from api.deps import get_current_user_id
from datetime import datetime, timezone

router = APIRouter()


@router.get("")
async def get_applications(
    status: str = None,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get user's applications."""
    if not db.client:
        return {"data": []}

    query = db.client.table("applications").select("*, opportunities(*)").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)

    result = query.execute()
    return {"data": result.data or []}


@router.post("")
async def create_application(
    application: Application,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Create application."""
    if not db.client:
        return {"message": "Application created (dev mode)", "application": application.model_dump()}

    result = db.client.table("applications").insert({
        "user_id": user_id,
        "opportunity_id": application.opportunity_id,
        "status": application.status,
        "notes": application.notes,
    }).execute()

    return {"message": "Application created", "application": result.data[0] if result.data else {}}


@router.get("/{application_id}")
async def get_application(
    application_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get single application with events."""
    if not db.client:
        raise HTTPException(status_code=404, detail="Application not found")

    result = (
        db.client.table("applications")
        .select("*, opportunities(*)")
        .eq("id", application_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Application not found")

    # Get events
    events = (
        db.client.table("application_events")
        .select("*")
        .eq("application_id", application_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "application": result.data[0],
        "events": events.data or [],
    }


@router.put("/{application_id}")
async def update_application(
    application_id: str,
    update: ApplicationUpdate,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Update application status."""
    if not db.client:
        return {"message": "Application updated (dev mode)"}

    # Verify ownership
    existing = (
        db.client.table("applications")
        .select("id")
        .eq("id", application_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Application not found")

    data = update.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Set applied_at when status changes to "applied"
    if data.get("status") == "applied":
        data["applied_at"] = datetime.now(timezone.utc).isoformat()

    result = db.client.table("applications").update(data).eq("id", application_id).execute()

    # Create event for status change
    if data.get("status"):
        db.client.table("application_events").insert({
            "application_id": application_id,
            "event_type": data["status"],
            "notes": data.get("notes", ""),
        }).execute()

    return {"message": "Application updated", "application": result.data[0] if result.data else data}


@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Delete application."""
    if not db.client:
        return {"message": "Application deleted (dev mode)"}

    db.client.table("applications").delete().eq("id", application_id).eq("user_id", user_id).execute()
    return {"message": "Application deleted"}


@router.post("/{application_id}/events")
async def add_event(
    application_id: str,
    event: ApplicationEvent,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Add event to application."""
    if not db.client:
        return {"message": "Event added (dev mode)", "event": event.model_dump()}

    # Verify ownership
    existing = (
        db.client.table("applications")
        .select("id")
        .eq("id", application_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Application not found")

    result = db.client.table("application_events").insert({
        "application_id": application_id,
        "event_type": event.event_type,
        "notes": event.notes,
    }).execute()

    return {"message": "Event added", "event": result.data[0] if result.data else {}}
