from fastapi import APIRouter, HTTPException, Depends
from models.schemas import Bookmark
from database.supabase_client import db
from api.deps import get_current_user_id

router = APIRouter()


@router.get("")
async def get_bookmarks(user_id: str = Depends(get_current_user_id)) -> dict:
    """Get user's bookmarks."""
    if not db.client:
        return {"data": []}

    result = db.client.table("bookmarks").select("*, opportunities(*)").eq("user_id", user_id).execute()
    return {"data": result.data or []}


@router.post("")
async def add_bookmark(
    bookmark: Bookmark,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Add a bookmark."""
    if not db.client:
        return {"message": "Bookmark added (dev mode)", "bookmark": bookmark.model_dump()}

    result = db.client.table("bookmarks").insert({
        "user_id": user_id,
        "opportunity_id": bookmark.opportunity_id,
        "notes": bookmark.notes,
    }).execute()

    return {"message": "Bookmark added", "bookmark": result.data[0] if result.data else {}}


@router.delete("/{bookmark_id}")
async def remove_bookmark(
    bookmark_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Remove a bookmark."""
    if not db.client:
        return {"message": "Bookmark removed (dev mode)"}

    db.client.table("bookmarks").delete().eq("id", bookmark_id).eq("user_id", user_id).execute()
    return {"message": "Bookmark removed"}


@router.get("/check/{opportunity_id}")
async def check_bookmark(
    opportunity_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Check if opportunity is bookmarked."""
    if not db.client:
        return {"is_bookmarked": False}

    result = (
        db.client.table("bookmarks")
        .select("id")
        .eq("user_id", user_id)
        .eq("opportunity_id", opportunity_id)
        .execute()
    )

    if result.data:
        return {"is_bookmarked": True, "bookmark_id": result.data[0]["id"]}
    return {"is_bookmarked": False}
