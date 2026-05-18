from fastapi import APIRouter, Depends
from models.schemas import MatchRequest, RecommendationRequest
from api.deps import get_current_user_id
from database.supabase_client import db
from config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/match")
async def match_opportunity(
    request: MatchRequest,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get AI match score for an opportunity."""
    from services.matching_service import match

    if not db.client:
        return {
            "opportunity_id": request.opportunity_id,
            "score": 0,
            "match_reasons": [],
            "concerns": [],
            "missing_skills": [],
            "preparation_suggestions": [],
        }

    # Get user profile
    profile_result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    # Get opportunity
    opp_result = db.client.table("opportunities").select("*").eq("id", request.opportunity_id).execute()
    if not opp_result.data:
        return {"error": "Opportunity not found"}
    opportunity = opp_result.data[0]

    result = await match(profile, opportunity)
    result["opportunity_id"] = request.opportunity_id
    return result


@router.post("/recommend")
async def get_recommendations(
    request: RecommendationRequest,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get AI-powered recommendations."""
    from services.matching_service import recommend

    if not db.client:
        return {"recommendations": [], "total": 0}

    # Get user profile
    profile_result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    # Get opportunities
    query = db.client.table("opportunities").select("*").eq("is_closed", False)
    if request.types:
        query = query.in_("type", request.types)
    opp_result = query.limit(50).execute()
    opportunities = opp_result.data or []

    recommendations = await recommend(profile, opportunities, request.limit)
    return {"recommendations": recommendations, "total": len(recommendations)}


@router.post("/analyze")
async def analyze_career(
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Analyze user's career trajectory."""
    from services.matching_service import career_analyze

    if not db.client:
        return {
            "current_stage": "unknown",
            "suggested_next_steps": [],
            "strengths": [],
            "areas_to_improve": [],
            "timeline": "",
        }

    # Get user profile
    profile_result = db.client.table("profiles").select("*").eq("user_id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    # Get application history
    app_result = db.client.table("applications").select("*").eq("user_id", user_id).execute()
    applications = app_result.data or []

    return await career_analyze(profile, applications)


@router.get("/providers")
async def get_ai_providers(
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get available AI providers (authenticated)."""
    providers = [
        {
            "name": "Groq",
            "status": "available" if settings.groq_api_key else "not_configured",
            "model": "llama-3.1-70b-versatile",
        },
        {
            "name": "Anthropic",
            "status": "available" if settings.anthropic_api_key else "not_configured",
            "model": "claude-3.5-sonnet",
        },
    ]
    return {"providers": providers}
