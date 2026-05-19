import pytest
from unittest.mock import patch, MagicMock


def test_parse_json_response_valid():
    """Test parsing valid JSON from LLM response."""
    from services.matching_service import _parse_json_response

    response = 'Here is the result: {"score": 85, "match_reasons": ["Python skills"]}'
    result = _parse_json_response(response)
    assert result is not None
    assert result["score"] == 85
    assert "Python skills" in result["match_reasons"]


def test_parse_json_response_invalid():
    """Test parsing invalid JSON returns None."""
    from services.matching_service import _parse_json_response

    assert _parse_json_response("") is None
    assert _parse_json_response("no json here") is None
    assert _parse_json_response("{broken json") is None


def test_parse_json_response_nested():
    """Test parsing JSON with nested objects."""
    from services.matching_service import _parse_json_response

    response = '{"data": {"nested": true}, "list": [1, 2, 3]}'
    result = _parse_json_response(response)
    assert result is not None
    assert result["data"]["nested"] is True
    assert result["list"] == [1, 2, 3]


def test_fallback_match_high_overlap():
    """Test fallback matching with high skill/interest overlap."""
    from services.matching_service import _fallback_match

    profile = {
        "skills": ["python", "react", "machine learning"],
        "interests": ["hackathons", "ai"],
    }
    opportunity = {
        "tags": ["python", "react", "ai", "hackathon"],
    }

    result = _fallback_match(profile, opportunity)
    assert result["score"] > 0
    assert len(result["match_reasons"]) > 0


def test_fallback_match_no_overlap():
    """Test fallback matching with no overlap."""
    from services.matching_service import _fallback_match

    profile = {
        "skills": ["java", "spring"],
        "interests": ["blockchain"],
    }
    opportunity = {
        "tags": ["python", "react"],
    }

    result = _fallback_match(profile, opportunity)
    assert result["score"] == 0
    assert result["match_reasons"] == []


def test_fallback_match_partial_overlap():
    """Test fallback matching with partial overlap."""
    from services.matching_service import _fallback_match

    profile = {
        "skills": ["python", "java"],
        "interests": [],
    }
    opportunity = {
        "tags": ["python", "react", "ai"],
    }

    result = _fallback_match(profile, opportunity)
    assert 0 < result["score"] < 100


@pytest.mark.asyncio
async def test_match_with_mock_llm():
    """Test match function with mocked LLM response."""
    from services.matching_service import match

    profile = {
        "name": "Test User",
        "university": "IIT Delhi",
        "year": 3,
        "skills": ["python", "react"],
        "interests": ["hackathons"],
    }
    opportunity = {
        "title": "Test Hackathon",
        "type": "hackathon",
        "description": "A test event",
        "difficulty": "beginner",
        "tags": ["python", "ai"],
    }

    mock_response = '{"score": 75, "match_reasons": ["Python match"], "concerns": [], "missing_skills": ["ai"], "preparation_suggestions": ["Learn ML basics"]}'

    with patch("services.matching_service._call_llm", return_value=mock_response):
        result = await match(profile, opportunity)

    assert result["score"] == 75
    assert "Python match" in result["match_reasons"]
    assert "ai" in result["missing_skills"]


@pytest.mark.asyncio
async def test_match_fallback_on_empty_llm():
    """Test match falls back to keyword matching when LLM returns empty."""
    from services.matching_service import match

    profile = {"skills": ["python"], "interests": ["hackathons"]}
    opportunity = {"tags": ["python"], "title": "Test", "type": "hackathon"}

    with patch("services.matching_service._call_llm", return_value=""):
        result = await match(profile, opportunity)

    assert "score" in result
    assert result["score"] >= 0


@pytest.mark.asyncio
async def test_recommend_orders_by_score():
    """Test recommend function returns results ordered by score."""
    from services.matching_service import recommend

    profile = {"skills": ["python"], "interests": ["hackathons"]}
    opportunities = [
        {"id": "opp-1", "title": "Opp 1", "tags": ["python"], "type": "hackathon"},
        {"id": "opp-2", "title": "Opp 2", "tags": ["java"], "type": "hackathon"},
        {"id": "opp-3", "title": "Opp 3", "tags": ["python", "ai"], "type": "hackathon"},
    ]

    # Mock match to return different scores
    async def mock_match(profile, opp):
        scores = {"opp-1": 50, "opp-2": 20, "opp-3": 80}
        return {"score": scores.get(opp.get("id"), 0), "match_reasons": [], "concerns": [], "missing_skills": [], "preparation_suggestions": []}

    with patch("services.matching_service.match", side_effect=mock_match):
        results = await recommend(profile, opportunities, limit=3)

    assert len(results) == 3
    assert results[0]["opportunity_id"] == "opp-3"
    assert results[1]["opportunity_id"] == "opp-1"
    assert results[2]["opportunity_id"] == "opp-2"
