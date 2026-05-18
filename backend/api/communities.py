from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from models.schemas import TeamRequest
from database.supabase_client import db
from api.deps import get_current_user_id

router = APIRouter()


@router.get("/activity")
async def get_peer_activity(
    opportunity_id: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
) -> dict:
    """Get peer activity feed."""
    if not db.client:
        return {"data": []}

    query = db.client.table("peer_activity").select("*")
    if opportunity_id:
        query = query.eq("opportunity_id", opportunity_id)

    result = query.order("created_at", desc=True).limit(limit).execute()
    return {"data": result.data or []}


@router.get("/leaderboard")
async def get_leaderboard(
    university: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
) -> dict:
    """Get campus leaderboard — aggregated from applications + peer_activity."""
    if not db.client:
        return {"leaderboard": []}

    # Get users with application counts
    apps = db.client.table("applications").select("user_id").execute()
    if not apps.data:
        return {"leaderboard": []}

    # Count applications per user
    user_counts: dict[str, int] = {}
    for app in apps.data:
        uid = app["user_id"]
        user_counts[uid] = user_counts.get(uid, 0) + 1

    # Get top N users
    top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    top_uids = [uid for uid, _ in top_users]

    # Batch fetch profiles for all top users (single query instead of N)
    profiles_result = db.client.table("profiles").select("user_id, name, university, avatar_url").in_("user_id", top_uids).execute()
    profiles_map = {p["user_id"]: p for p in (profiles_result.data or [])}

    # Batch fetch wins for all top users (single query instead of N)
    wins_result = db.client.table("peer_activity").select("user_id").in_("user_id", top_uids).eq("action", "won").execute()
    wins_map: dict[str, int] = {}
    for w in (wins_result.data or []):
        uid = w["user_id"]
        wins_map[uid] = wins_map.get(uid, 0) + 1

    leaderboard = []
    for rank, (uid, app_count) in enumerate(top_users, 1):
        profile = profiles_map.get(uid, {})
        name = profile.get("name", "Unknown")
        uni = profile.get("university", "")
        win_count = wins_map.get(uid, 0)

        leaderboard.append({
            "rank": rank,
            "user_id": uid,
            "user_name": f"{name} from {uni}" if uni else name,
            "points": app_count * 50 + win_count * 200,
            "wins": win_count,
            "applications": app_count,
        })

    return {"leaderboard": leaderboard}


# --- Team Finder ---

@router.post("/team-find")
async def create_team_request(
    request: TeamRequest,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Create a team request for a hackathon."""
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    data = {
        "user_id": user_id,
        "opportunity_id": request.opportunity_id,
        "looking_for": request.looking_for,
        "description": request.description,
    }

    result = db.client.table("team_requests").upsert(data, on_conflict="user_id,opportunity_id").execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create team request")

    return {"message": "Team request created", "data": result.data[0]}


@router.get("/team-find/{opportunity_id}")
async def get_team_requests(
    opportunity_id: str,
    limit: int = Query(20, le=50),
) -> dict:
    """Get open team requests for an opportunity."""
    if not db.client:
        return {"teams": []}

    result = (
        db.client.table("team_requests")
        .select("*, profiles:user_id(name, university, skills)")
        .eq("opportunity_id", opportunity_id)
        .eq("status", "open")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return {"teams": result.data or []}


@router.post("/team-find/{request_id}/join")
async def join_team(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Join an existing team request."""
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    # Fetch the team request
    team = db.client.table("team_requests").select("*").eq("id", request_id).execute()
    if not team.data:
        raise HTTPException(status_code=404, detail="Team request not found")

    team_data = team.data[0]

    # Can't join your own team
    if team_data["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="You cannot join your own team request")

    # Check if already a member
    members = team_data.get("members", []) or []
    if user_id in members:
        raise HTTPException(status_code=400, detail="You are already a member of this team")

    # Check max members
    max_members = team_data.get("max_members", 4)
    if len(members) + 1 >= max_members:  # +1 for the owner
        raise HTTPException(status_code=400, detail="Team is already full")

    # Add user to members
    members.append(user_id)
    result = (
        db.client.table("team_requests")
        .update({"members": members})
        .eq("id", request_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to join team")

    return {"message": "Joined team successfully", "data": result.data[0]}


@router.delete("/team-find/{request_id}")
async def delete_team_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Delete own team request."""
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    result = (
        db.client.table("team_requests")
        .delete()
        .eq("id", request_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Team request not found")

    return {"message": "Team request deleted"}


# --- University ---

@router.get("/university/{slug}")
async def get_university(
    slug: str,
    limit: int = Query(20, le=50),
) -> dict:
    """Get university info, opportunities, and peer activity."""
    if not db.client:
        return {"university": None, "opportunities": [], "activity": []}

    # Look up university by name (slug is URL-encoded name)
    university_name = slug.replace("-", " ").title()

    uni_result = (
        db.client.table("universities")
        .select("*")
        .ilike("name", f"%{university_name}%")
        .limit(1)
        .execute()
    )

    if not uni_result.data:
        # Try exact match on common variations
        uni_result = (
            db.client.table("universities")
            .select("*")
            .ilike("name", f"%{slug}%")
            .limit(1)
            .execute()
        )

    university = uni_result.data[0] if uni_result.data else {"name": university_name, "domain": "", "academic_calendar_json": {}}

    # Get profiles from this university
    profiles_result = (
        db.client.table("profiles")
        .select("user_id")
        .ilike("university", f"%{university_name}%")
        .limit(100)
        .execute()
    )

    user_ids = [p["user_id"] for p in (profiles_result.data or [])]

    # Get opportunities bookmarked/applied by users from this university
    opportunities = []
    if user_ids:
        # Get bookmarked opportunity IDs
        bookmarks = (
            db.client.table("bookmarks")
            .select("opportunity_id")
            .in_("user_id", user_ids[:50])
            .execute()
        )
        app_result = (
            db.client.table("applications")
            .select("opportunity_id")
            .in_("user_id", user_ids[:50])
            .execute()
        )

        opp_ids = set()
        for b in (bookmarks.data or []):
            opp_ids.add(b["opportunity_id"])
        for a in (app_result.data or []):
            opp_ids.add(a["opportunity_id"])

        if opp_ids:
            opps = (
                db.client.table("opportunities")
                .select("*")
                .in_("id", list(opp_ids)[:limit])
                .execute()
            )
            opportunities = opps.data or []

    # Get peer activity from this university
    activity = []
    if user_ids:
        act_result = (
            db.client.table("peer_activity")
            .select("*")
            .in_("user_id", user_ids[:50])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        activity = act_result.data or []

    return {
        "university": university,
        "opportunities": opportunities,
        "activity": activity,
        "student_count": len(user_ids),
    }


@router.get("/success-stories")
async def get_success_stories(limit: int = Query(10, le=50)) -> dict:
    """Get success stories from students (peer_activity where action='won')."""
    if not db.client:
        return {"stories": []}

    result = (
        db.client.table("peer_activity")
        .select("*")
        .eq("action", "won")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return {"stories": result.data or []}
