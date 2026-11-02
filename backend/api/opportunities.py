from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from models.schemas import Opportunity
from database.supabase_client import db
from api.deps import get_current_user_id

import time

from models.schemas import OpportunityType

router = APIRouter()

# Public landing-page counts are cheap to cache: they change only when a
# scrape lands, and every anonymous visitor would otherwise cost one count
# query per type.
STATS_TTL_SECONDS = 60
_stats_cache: dict = {"at": 0.0, "value": None}


def _reset_stats_cache() -> None:
    _stats_cache["at"] = 0.0
    _stats_cache["value"] = None


@router.get("/stats")
async def get_opportunity_stats() -> dict:
    """Public per-type opportunity counts for the landing page.

    Returns ``{"by_type": {type: count}, "total": int, "available": bool}``.
    ``available`` is False when the database is not configured or a query
    fails, so the frontend can fall back to its static numbers.
    """
    now = time.monotonic()
    cached = _stats_cache["value"]
    if cached is not None and now - _stats_cache["at"] < STATS_TTL_SECONDS:
        return cached

    types = [t.value for t in OpportunityType]
    empty = {"by_type": {t: 0 for t in types}, "total": 0, "available": False}
    if not db.client:
        return empty

    by_type: dict[str, int] = {}
    try:
        for t in types:
            result = (
                db.client.table("opportunities")
                .select("id", count="exact", head=True)
                .eq("type", t)
                .execute()
            )
            by_type[t] = int(result.count or 0)
    except Exception:
        return empty

    value = {"by_type": by_type, "total": sum(by_type.values()), "available": True}
    _stats_cache["at"] = now
    _stats_cache["value"] = value
    return value


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
