from fastapi import APIRouter, HTTPException, Depends
from models.schemas import Profile, ProfileUpdate
from database.supabase_client import db
from api.deps import get_current_user_id

router = APIRouter()


@router.get("")
async def get_profile(user_id: str = Depends(get_current_user_id)) -> dict:
    """Get current user profile."""
    if not db.client:
        return {
            "id": user_id,
            "user_id": user_id,
            "name": "Dev User",
            "university": "IIT Madras",
            "year": 3,
            "bio": "Passionate about building things",
            "skills": ["Python", "React"],
            "interests": ["Open Source", "Hackathons"],
        }

    result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()
    if not result.data:
        # Create a blank profile on first access
        db.client.table("profiles").insert({
            "user_id": user_id,
            "name": "",
        }).execute()
        result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()

    return result.data[0] if result.data else {}


@router.put("")
async def update_profile(
    profile: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Update user profile."""
    if not db.client:
        return {"message": "Profile updated (dev mode)", "profile": profile.model_dump()}

    data = profile.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    data["user_id"] = user_id
    result = db.client.table("profiles").upsert(data, on_conflict="user_id").execute()

    return {"message": "Profile updated", "profile": result.data[0] if result.data else data}


@router.get("/skills")
async def get_skills(user_id: str = Depends(get_current_user_id)) -> dict:
    """Get user's skills."""
    if not db.client:
        return {"skills": ["Python", "React"]}

    result = db.client.table("profiles").select("skills").eq("user_id", user_id).execute()
    if not result.data:
        return {"skills": []}

    return {"skills": result.data[0].get("skills", [])}


@router.post("/skills")
async def add_skill(
    skill: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Add a skill."""
    if not db.client:
        return {"skills": [skill]}

    # Get current skills
    result = db.client.table("profiles").select("skills").eq("user_id", user_id).execute()
    current_skills = result.data[0].get("skills", []) if result.data else []

    if skill not in current_skills:
        current_skills.append(skill)
        db.client.table("profiles").update({"skills": current_skills}).eq("user_id", user_id).execute()

    return {"skills": current_skills}


@router.delete("/skills/{skill}")
async def remove_skill(
    skill: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Remove a skill."""
    if not db.client:
        return {"skills": []}

    result = db.client.table("profiles").select("skills").eq("user_id", user_id).execute()
    current_skills = result.data[0].get("skills", []) if result.data else []

    if skill in current_skills:
        current_skills.remove(skill)
        db.client.table("profiles").update({"skills": current_skills}).eq("user_id", user_id).execute()

    return {"skills": current_skills}
