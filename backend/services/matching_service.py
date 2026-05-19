import json
import logging
import asyncio
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Singleton LLM clients
_groq_client = None
_anthropic_client = None


def _get_groq():
    global _groq_client
    if _groq_client is None and settings.groq_api_key:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=settings.groq_api_key)
        except Exception as exc:
            logger.warning(f"Failed to initialize Groq client: {exc}")
    return _groq_client


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        try:
            import anthropic
            _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        except Exception as exc:
            logger.warning(f"Failed to initialize Anthropic client: {exc}")
    return _anthropic_client


def _parse_json_response(response: str) -> Optional[dict]:
    """Extract JSON from LLM response text."""
    if not response:
        return None
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse JSON from LLM response")
    return None


async def _call_llm(prompt: str) -> str:
    """Call LLM with a prompt, trying Groq first then Anthropic."""
    groq = _get_groq()
    if groq:
        try:
            response = groq.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.warning(f"Groq call failed: {exc}")

    anthropic_client = _get_anthropic()
    if anthropic_client:
        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as exc:
            logger.warning(f"Anthropic call failed: {exc}")

    return ""


async def match(user_profile: dict, opportunity: dict) -> dict:
    """Calculate match score between user profile and opportunity."""
    prompt = f"""Analyze how well this student profile matches this opportunity.

Student Profile:
- Name: {user_profile.get('name', 'Unknown')}
- University: {user_profile.get('university', 'Unknown')}
- Year: {user_profile.get('year', 'Unknown')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Interests: {', '.join(user_profile.get('interests', []))}

Opportunity:
- Title: {opportunity.get('title', '')}
- Type: {opportunity.get('type', '')}
- Description: {opportunity.get('description', '')[:500]}
- Difficulty: {opportunity.get('difficulty', '')}
- Tags: {', '.join(opportunity.get('tags', []))}

Respond in JSON format:
{{
    "score": <0-100>,
    "match_reasons": [<list of reasons this is a good match>],
    "concerns": [<list of potential concerns>],
    "missing_skills": [<skills the student should learn>],
    "preparation_suggestions": [<how to prepare>]
}}"""

    response = await _call_llm(prompt)
    parsed = _parse_json_response(response)

    if parsed and "score" in parsed:
        return parsed

    # Fallback: basic keyword matching
    return _fallback_match(user_profile, opportunity)


def _fallback_match(user_profile: dict, opportunity: dict) -> dict:
    """Simple keyword-based matching as fallback."""
    user_skills = set(s.lower() for s in user_profile.get("skills", []))
    user_interests = set(i.lower() for i in user_profile.get("interests", []))
    opp_tags = set(t.lower() for t in opportunity.get("tags", []))

    skill_overlap = user_skills & opp_tags
    interest_overlap = user_interests & opp_tags

    score = min(100, len(skill_overlap) * 25 + len(interest_overlap) * 15)

    reasons = []
    if skill_overlap:
        reasons.append(f"Skills match: {', '.join(skill_overlap)}")
    if interest_overlap:
        reasons.append(f"Interests align: {', '.join(interest_overlap)}")

    return {
        "score": score,
        "match_reasons": reasons,
        "concerns": [],
        "missing_skills": [],
        "preparation_suggestions": [],
    }


async def recommend(user_profile: dict, opportunities: list, limit: int = 10) -> list:
    """Score and rank multiple opportunities for a user using concurrent LLM calls."""
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent LLM calls

    async def bounded_match(opp: dict) -> dict:
        async with semaphore:
            result = await match(user_profile, opp)
            return {
                "opportunity_id": opp.get("id"),
                "score": result.get("score", 0),
                "reason": result.get("match_reasons", [""])[0] if result.get("match_reasons") else "",
            }

    scored = await asyncio.gather(*[bounded_match(opp) for opp in opportunities])
    scored_list = list(scored)
    scored_list.sort(key=lambda x: x["score"], reverse=True)
    return scored_list[:limit]


async def career_analyze(user_profile: dict, applications: list) -> dict:
    """Analyze career trajectory based on profile and application history."""
    prompt = f"""Analyze this student's career trajectory and provide guidance.

Student Profile:
- Name: {user_profile.get('name', 'Unknown')}
- University: {user_profile.get('university', 'Unknown')}
- Year: {user_profile.get('year', 'Unknown')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Interests: {', '.join(user_profile.get('interests', []))}

Application History ({len(applications)} applications):
{', '.join(a.get('status', '') for a in applications[:10])}

Respond in JSON format:
{{
    "current_stage": "<assessment of where they are>",
    "suggested_next_steps": [<3-5 actionable next steps>],
    "strengths": [<their strengths>],
    "areas_to_improve": [<areas to work on>],
    "timeline": "<estimated timeline to next milestone>"
}}"""

    response = await _call_llm(prompt)
    parsed = _parse_json_response(response)

    if parsed and "current_stage" in parsed:
        return parsed

    return {
        "current_stage": "early_explorer",
        "suggested_next_steps": ["Apply to beginner-friendly hackathons", "Start an open source contribution"],
        "strengths": user_profile.get("skills", []),
        "areas_to_improve": [],
        "timeline": "6-12 months to first significant achievement",
    }
