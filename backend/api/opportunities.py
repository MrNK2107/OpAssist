from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from models.schemas import Opportunity
from database.supabase_client import db
from api.deps import get_current_user_id

router = APIRouter()


@router.get("")
async def get_opportunities(
    type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
) -> dict:
    """Get list of opportunities with filters."""
    if not db.client:
        return {"data": [], "total": 0, "limit": limit, "offset": offset}

    query = db.client.table("opportunities").select("*", count="exact")

    if type:
        query = query.eq("type", type)
    if source:
        query = query.eq("source", source)
    if difficulty:
        query = query.eq("difficulty", difficulty)
    if search:
        query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")

    # Apply pagination and get count in single query
    result = query.range(offset, offset + limit - 1).execute()

    return {
        "data": result.data or [],
        "total": result.count if result.count is not None else 0,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: str) -> dict:
    """Get single opportunity details."""
    if not db.client:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    result = db.client.table("opportunities").select("*").eq("id", opportunity_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return result.data[0]


@router.post("/{opportunity_id}/match")
async def match_opportunity(
    opportunity_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get AI match score for opportunity."""
    from services.matching_service import match

    if not db.client:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Verify opportunity exists
    result = db.client.table("opportunities").select("*").eq("id", opportunity_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opportunity = result.data[0]

    # Get user profile
    profile_result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    match_result = await match(profile, opportunity)
    match_result["opportunity_id"] = opportunity_id
    return match_result
