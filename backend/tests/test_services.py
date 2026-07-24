import pytest
from unittest.mock import patch, MagicMock


class TestMatchingService:
    def test_parse_json_valid(self):
        from services.matching_service import _parse_json_response
        result = _parse_json_response('{"score": 85, "match_reasons": ["good"]}')
        assert result is not None
        assert result["score"] == 85

    def test_parse_json_with_prefix(self):
        from services.matching_service import _parse_json_response
        result = _parse_json_response('Here is the result: {"score": 75}')
        assert result is not None
        assert result["score"] == 75

    def test_parse_json_invalid_returns_none(self):
        from services.matching_service import _parse_json_response
        assert _parse_json_response("") is None
        assert _parse_json_response("no json") is None
        assert _parse_json_response("{broken") is None

    def test_parse_json_nested(self):
        from services.matching_service import _parse_json_response
        result = _parse_json_response('{"data": {"nested": true}, "list": [1, 2]}')
        assert result is not None
        assert result["data"]["nested"] is True
        assert result["list"] == [1, 2]

    def test_fallback_match_high_overlap(self):
        from services.matching_service import _fallback_match
        profile = {"skills": ["python", "react"], "interests": ["hackathons"]}
        opportunity = {"tags": ["python", "react", "hackathon"]}
        result = _fallback_match(profile, opportunity)
        assert result["score"] >= 50
        assert len(result["match_reasons"]) > 0

    def test_fallback_match_no_overlap(self):
        from services.matching_service import _fallback_match
        profile = {"skills": ["java"], "interests": ["blockchain"]}
        opportunity = {"tags": ["python"]}
        result = _fallback_match(profile, opportunity)
        assert result["score"] == 0
        assert result["match_reasons"] == []

    def test_fallback_match_partial(self):
        from services.matching_service import _fallback_match
        profile = {"skills": ["python"], "interests": []}
        opportunity = {"tags": ["python", "react"]}
        result = _fallback_match(profile, opportunity)
        assert 0 < result["score"] < 100

    def test_fallback_match_empty_profile(self):
        from services.matching_service import _fallback_match
        profile = {"skills": [], "interests": []}
        opportunity = {"tags": ["python"]}
        result = _fallback_match(profile, opportunity)
        assert result["score"] == 0

    @pytest.mark.asyncio
    async def test_match_with_mock_llm(self):
        from services.matching_service import match
        profile = {"skills": ["python"], "interests": []}
        opportunity = {"title": "Test", "type": "hackathon", "description": "", "difficulty": "", "tags": []}
        with patch("services.matching_service._call_llm", return_value='{"score": 80, "match_reasons": ["python match"], "concerns": [], "missing_skills": [], "preparation_suggestions": []}'):
            result = await match(profile, opportunity)
        assert result["score"] == 80

    @pytest.mark.asyncio
    async def test_match_fallback_on_empty_llm(self):
        from services.matching_service import match
        profile = {"skills": ["python"], "interests": []}
        opportunity = {"tags": ["python"], "title": "Test", "type": "hackathon"}
        with patch("services.matching_service._call_llm", return_value=""):
            result = await match(profile, opportunity)
        assert result["score"] >= 0

    @pytest.mark.asyncio
    async def test_match_fallback_on_invalid_json(self):
        from services.matching_service import match
        profile = {"skills": ["python"], "interests": []}
        opportunity = {"tags": ["python"], "title": "Test", "type": "hackathon"}
        with patch("services.matching_service._call_llm", return_value="not json"):
            result = await match(profile, opportunity)
        assert "score" in result

    @pytest.mark.asyncio
    async def test_recommend_orders_by_score(self):
        from services.matching_service import recommend
        profile = {"skills": ["python"], "interests": []}
        opportunities = [
            {"id": "opp-1", "title": "A", "tags": ["python"], "type": "hackathon"},
            {"id": "opp-2", "title": "B", "tags": ["java"], "type": "hackathon"},
        ]
        async def mock_match(p, o):
            scores = {"opp-1": 80, "opp-2": 20}
            return {"score": scores.get(o.get("id"), 0), "match_reasons": [], "concerns": [], "missing_skills": [], "preparation_suggestions": []}
        with patch("services.matching_service.match", side_effect=mock_match):
            results = await recommend(profile, opportunities, limit=2)
        assert results[0]["opportunity_id"] == "opp-1"
        assert results[1]["opportunity_id"] == "opp-2"

    @pytest.mark.asyncio
    async def test_recommend_respects_limit(self):
        from services.matching_service import recommend
        profile = {"skills": [], "interests": []}
        opportunities = [{"id": f"opp-{i}", "title": str(i), "tags": [], "type": "hackathon"} for i in range(10)]
        async def mock_match(p, o):
            return {"score": 50, "match_reasons": [], "concerns": [], "missing_skills": [], "preparation_suggestions": []}
        with patch("services.matching_service.match", side_effect=mock_match):
            results = await recommend(profile, opportunities, limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_career_analyze_with_llm(self):
        from services.matching_service import career_analyze
        profile = {"skills": ["python"], "interests": [], "name": "Test", "university": "MIT", "year": 3}
        applications = [{"status": "applied"}]
        with patch("services.matching_service._call_llm", return_value='{"current_stage": "intermediate", "suggested_next_steps": ["do hackathons"], "strengths": ["python"], "areas_to_improve": [], "timeline": "6 months"}'):
            result = await career_analyze(profile, applications)
        assert result["current_stage"] == "intermediate"

    @pytest.mark.asyncio
    async def test_career_analyze_fallback(self):
        from services.matching_service import career_analyze
        profile = {"skills": ["python"], "interests": [], "name": "Test", "university": "", "year": 0}
        applications = []
        with patch("services.matching_service._call_llm", return_value=""):
            result = await career_analyze(profile, applications)
        assert "current_stage" in result

    def test_get_groq_returns_none_without_key(self):
        from services.matching_service import _get_groq
        with patch("services.matching_service.settings") as mock_settings:
            mock_settings.groq_api_key = ""
            client = _get_groq()
        assert client is None

    def test_get_anthropic_returns_none_without_key(self):
        from services.matching_service import _get_anthropic
        with patch("services.matching_service.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            client = _get_anthropic()
        assert client is None


class TestScraperService:
    def test_run_scraper_success(self):
        from services.scraper_service import run_scraper
        mock_scraper = MagicMock()
        mock_scraper.run.return_value = [{"title": "Test"}]
        mock_class = MagicMock(return_value=mock_scraper)
        results, error = run_scraper(mock_class)
        assert len(results) == 1
        assert error is None

    def test_run_scraper_error(self):
        from services.scraper_service import run_scraper
        mock_class = MagicMock(side_effect=Exception("scraper failed"), __name__="MockScraper")
        results, error = run_scraper(mock_class)
        assert results == []
        assert error is not None

    def test_upsert_opportunities_empty(self):
        from services.scraper_service import upsert_opportunities
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.upsert_opportunity.return_value = MagicMock(data=[{"id": "new"}])
            result = upsert_opportunities([], "test-source")
        assert result["new"] == 0
        assert result["errors"] == 0

    def test_upsert_opportunities_skips_empty_url(self):
        from services.scraper_service import upsert_opportunities
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = MagicMock()
            result = upsert_opportunities([{"title": "No URL"}], "test")
        assert result["errors"] == 1

    def test_upsert_opportunities_success(self):
        from services.scraper_service import upsert_opportunities
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.upsert_opportunity.return_value = MagicMock(data=[{"id": "new-1"}])
            items = [{"title": "Test Hackathon", "link": "https://example.com/hackathon", "type": "hackathon"}]
            result = upsert_opportunities(items, "test")
        assert result["new"] == 1

    def test_delete_expired_no_db(self):
        from services.scraper_service import delete_expired
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = None
            count = delete_expired()
        assert count == 0

    def test_delete_expired_with_data(self):
        from services.scraper_service import delete_expired
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.not_.is_.return_value.lt.return_value.execute.return_value = MagicMock(data=[{"id": "1"}], count=2)
            count = delete_expired()
        assert count == 2

    def test_deduplicate_no_db(self):
        from services.scraper_service import deduplicate_opportunities
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = None
            count = deduplicate_opportunities()
        assert count == 0

    def test_deduplicate_no_dupes(self):
        from services.scraper_service import deduplicate_opportunities
        with patch("services.scraper_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
                {"id": "1", "title": "Unique", "organizer": "Org1", "url": "a.com", "source": "test", "deadline": None, "description": ""},
            ])
            count = deduplicate_opportunities()
        assert count == 0

    def test_run_full_scrape(self):
        from services.scraper_service import run_full_scrape
        with patch("services.scraper_service.run_scraper") as mock_run:
            mock_run.return_value = ([], None)
            with patch("services.scraper_service.upsert_opportunities") as mock_upsert:
                mock_upsert.return_value = {"new": 1, "updated": 0, "errors": 0}
                with patch("services.scraper_service.deduplicate_opportunities") as mock_dedup:
                    mock_dedup.return_value = 0
                    with patch("services.scraper_service.delete_expired") as mock_exp:
                        mock_exp.return_value = 0
                        result = run_full_scrape()
        assert "duration_seconds" in result
        assert "sources" in result


class TestNotificationService:
    def test_get_upcoming_deadline_opportunities(self):
        from services.notification_service import get_upcoming_deadline_opportunities
        with patch("services.notification_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.gte.return_value.lte.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "opp-1", "title": "Test", "deadline": "2026-07-01"}])
            results = get_upcoming_deadline_opportunities(days=3)
        assert len(results) == 1

    def test_get_upcoming_deadline_no_db(self):
        from services.notification_service import get_upcoming_deadline_opportunities
        with patch("services.notification_service.db") as mock_db:
            mock_db.client = None
            results = get_upcoming_deadline_opportunities()
        assert results == []

    def test_get_user_notifications_from_db(self):
        from services.notification_service import get_user_notifications
        with patch("services.notification_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "n-1", "is_read": False}])
            results = get_user_notifications("user-1")
        assert len(results) == 1

    def test_get_user_notifications_fallback(self):
        from services.notification_service import get_user_notifications
        with patch("services.notification_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
                MagicMock(data=[]), MagicMock(data=[]),
            ]
            results = get_user_notifications("user-1")
        assert results == []

    def test_generate_deadline_notifications(self):
        from services.notification_service import _generate_deadline_notifications
        with patch("services.notification_service.db") as mock_db:
            mock_db.client = MagicMock()
            mock_db.client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
                MagicMock(data=[{"opportunity_id": "opp-1"}]),
                MagicMock(data=[]),
            ]
            from datetime import datetime, timedelta, timezone
            future = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()
            mock_db.client.table.return_value.select.return_value.in_.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(data=[{"id": "opp-1", "title": "Test", "deadline": future}])
            results = _generate_deadline_notifications("user-1")
        assert len(results) > 0


class TestScheduler:
    def test_scheduler_import(self):
        from scheduler.jobs import scheduler, start_scheduler, stop_scheduler
        assert scheduler is not None

    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self):
        from scheduler.jobs import start_scheduler, stop_scheduler
        try:
            start_scheduler(scrape_interval_hours=24)
            assert True
        finally:
            stop_scheduler()
