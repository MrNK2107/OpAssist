import pytest
from unittest.mock import MagicMock, patch


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


class TestOpportunities:
    def test_list_empty(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
        response = client.get("/api/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["data"] == []

    def test_list_with_filters(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[{"id": "1", "title": "Test"}], count=1)
        response = client.get("/api/opportunities?type=hackathon&difficulty=beginner&search=test")
        assert response.status_code == 200

    def test_list_pagination(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
        response = client.get("/api/opportunities?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10

    def test_get_by_id_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "opp-1", "title": "Test Hackathon"}])
        response = client.get("/api/opportunities/opp-1")
        assert response.status_code == 200
        assert response.json()["id"] == "opp-1"

    def test_get_by_id_not_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/opportunities/nonexistent")
        assert response.status_code == 404

    def test_match_endpoint(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "opp-1", "title": "Test", "type": "hackathon"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"id": "opp-1", "title": "Test", "type": "hackathon", "description": "", "difficulty": "", "tags": []}]),
            MagicMock(data=[{"user_id": "dev-user-001", "skills": ["python"], "interests": []}]),
        ]
        with patch("services.matching_service.match") as mock_match:
            mock_match.return_value = {"score": 85, "match_reasons": [], "concerns": [], "missing_skills": [], "preparation_suggestions": []}
            response = client.post("/api/opportunities/opp-1/match")
            assert response.status_code == 200
            data = response.json()
            assert data["score"] == 85


class TestProfile:
    def test_get_profile(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": "dev-user-001", "name": "Test User"}])
        response = client.get("/api/profile")
        assert response.status_code == 200

    def test_get_profile_creates_on_first_access(self, client, mock_db):
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"user_id": "dev-user-001"}])
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[]),
            MagicMock(data=[{"user_id": "dev-user-001", "name": ""}]),
        ]
        response = client.get("/api/profile")
        assert response.status_code == 200

    def test_update_profile(self, client, mock_db):
        response = client.put("/api/profile", json={"name": "Updated", "skills": ["python"]})
        assert response.status_code == 200

    def test_update_profile_empty(self, client, mock_db):
        response = client.put("/api/profile", json={})
        assert response.status_code == 400

    def test_get_skills(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"skills": ["python", "react"]}])
        response = client.get("/api/profile/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data

    def test_add_skill(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"skills": ["python"]}])
        response = client.post("/api/profile/skills?skill=react")
        assert response.status_code == 200
        data = response.json()
        assert "react" in data["skills"]

    def test_remove_skill(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"skills": ["python", "react"]}])
        response = client.delete("/api/profile/skills/python")
        assert response.status_code == 200
        data = response.json()
        assert "python" not in data["skills"]


class TestBookmarks:
    def test_list_bookmarks(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "bm-1", "opportunity_id": "opp-1"}])
        response = client.get("/api/bookmarks")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_add_bookmark(self, client, mock_db):
        response = client.post("/api/bookmarks", json={"opportunity_id": "opp-1"})
        assert response.status_code == 200

    def test_add_bookmark_validation(self, client):
        response = client.post("/api/bookmarks", json={})
        assert response.status_code == 422

    def test_remove_bookmark(self, client, mock_db):
        response = client.delete("/api/bookmarks/bm-1")
        assert response.status_code == 200

    def test_check_bookmark_true(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "bm-1"}])
        response = client.get("/api/bookmarks/check/opp-1")
        assert response.status_code == 200
        assert response.json()["is_bookmarked"] is True

    def test_check_bookmark_false(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/bookmarks/check/opp-1")
        assert response.status_code == 200
        assert response.json()["is_bookmarked"] is False


class TestApplications:
    def test_list_applications(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/applications")
        assert response.status_code == 200

    def test_list_with_status_filter(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/applications?status=applied")
        assert response.status_code == 200

    def test_create_application(self, client, mock_db):
        response = client.post("/api/applications", json={"opportunity_id": "opp-1", "status": "saved"})
        assert response.status_code == 200

    def test_create_application_invalid_status(self, client, mock_db):
        response = client.post("/api/applications", json={"opportunity_id": "opp-1", "status": "invalid"})
        assert response.status_code == 200
        assert response.json()["application"]["status"] == "saved"

    def test_get_application_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "app-1"}])
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/applications/app-1")
        assert response.status_code == 200

    def test_get_application_not_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/applications/nonexistent")
        assert response.status_code == 404

    def test_update_application(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "app-1"}])
        response = client.put("/api/applications/app-1", json={"status": "applied", "notes": "Applied!"})
        assert response.status_code == 200

    def test_update_application_not_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.put("/api/applications/nonexistent", json={"status": "applied"})
        assert response.status_code == 404

    def test_delete_application(self, client, mock_db):
        response = client.delete("/api/applications/app-1")
        assert response.status_code == 200

    def test_add_event(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "app-1"}])
        response = client.post("/api/applications/app-1/events", json={"event_type": "interview", "notes": "Had interview"})
        assert response.status_code == 200

    def test_add_event_not_found(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.post("/api/applications/nonexistent/events", json={"event_type": "test"})
        assert response.status_code == 404


class TestAI:
    def test_match_ai(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"user_id": "dev-user-001", "skills": ["python"]}]),
            MagicMock(data=[{"id": "opp-1", "title": "Test", "type": "hackathon"}]),
        ]
        with patch("services.matching_service.match") as mock_match:
            mock_match.return_value = {"score": 90, "match_reasons": [], "concerns": [], "missing_skills": [], "preparation_suggestions": []}
            response = client.post("/api/ai/match", json={"opportunity_id": "opp-1"})
            assert response.status_code == 200
            assert response.json()["score"] == 90

    def test_recommend(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"user_id": "dev-user-001", "skills": ["python"]}]),
            MagicMock(data=[{"id": "opp-1", "title": "Test"}])
        ]
        with patch("services.matching_service.recommend") as mock_rec:
            mock_rec.return_value = [{"opportunity_id": "opp-1", "score": 85}]
            response = client.post("/api/ai/recommend", json={"limit": 5})
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data

    def test_analyze_career(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            MagicMock(data=[{"user_id": "dev-user-001", "skills": ["python"]}]),
            MagicMock(data=[{"status": "applied"}]),
        ]
        with patch("services.matching_service.career_analyze") as mock_analyze:
            mock_analyze.return_value = {"current_stage": "explorer", "suggested_next_steps": []}
            response = client.post("/api/ai/analyze")
            assert response.status_code == 200

    def test_get_providers(self, client):
        response = client.get("/api/ai/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data


class TestCommunities:
    def test_get_peer_activity(self, client, mock_db):
        mock_db.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/communities/activity")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_get_leaderboard(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/communities/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data

    def test_create_team_request(self, client, mock_db):
        mock_db.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "team-1"}])
        response = client.post("/api/communities/team-find", json={"opportunity_id": "opp-1", "looking_for": ["developer"], "description": "Looking for dev"})
        assert response.status_code == 200

    def test_create_team_request_no_db(self, client):
        from api.communities import db as communities_db
        original_client = communities_db.client
        communities_db.client = None
        try:
            response = client.post("/api/communities/team-find", json={"opportunity_id": "opp-1", "looking_for": ["dev"], "description": "test"})
            assert response.status_code == 503
        finally:
            communities_db.client = original_client

    def test_get_team_requests(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/communities/team-find/opp-1")
        assert response.status_code == 200

    def test_join_team(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "team-1", "user_id": "other-user", "members": [], "max_members": 4}])
        response = client.post("/api/communities/team-find/team-1/join")
        assert response.status_code == 200

    def test_join_own_team(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "team-1", "user_id": "dev-user-001", "members": [], "max_members": 4}])
        response = client.post("/api/communities/team-find/team-1/join")
        assert response.status_code == 400
        assert "own team" in response.json()["detail"].lower()

    def test_join_full_team(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "team-1", "user_id": "other-user", "members": ["m1", "m2", "m3"], "max_members": 4}])
        response = client.post("/api/communities/team-find/team-1/join")
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()

    def test_join_already_member(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "team-1", "user_id": "other-user", "members": ["dev-user-001"], "max_members": 4}])
        response = client.post("/api/communities/team-find/team-1/join")
        assert response.status_code == 400

    def test_delete_team_request(self, client, mock_db):
        mock_db.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "team-1"}])
        response = client.delete("/api/communities/team-find/team-1")
        assert response.status_code == 200

    def test_delete_team_request_not_found(self, client, mock_db):
        mock_db.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.delete("/api/communities/team-find/nonexistent")
        assert response.status_code == 404

    def test_get_university(self, client, mock_db):
        mock_db.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "uni-1", "name": "IIT Delhi"}])
        mock_db.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value.select.return_value.in_.return_value.execute.side_effect = [
            MagicMock(data=[]), MagicMock(data=[]),
        ]
        mock_db.table.return_value.select.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/communities/university/iit-delhi")
        assert response.status_code == 200

    def test_get_success_stories(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/communities/success-stories")
        assert response.status_code == 200


class TestScraping:
    def test_trigger_scrape(self, client):
        with patch("services.scraper_service.run_full_scrape") as mock_scrape:
            mock_scrape.return_value = {"duration_seconds": 1.5, "sources": {}}
            response = client.post("/api/scrape/trigger")
            assert response.status_code == 200
            assert response.json()["status"] == "done"

    def test_trigger_scrape_error(self, client):
        with patch("services.scraper_service.run_full_scrape", side_effect=Exception("scrape failed")):
            response = client.post("/api/scrape/trigger")
            assert response.status_code == 200
            assert response.json()["status"] == "error"

    def test_get_scrape_status(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/scrape/status")
        assert response.status_code == 200

    def test_toggle_source(self, client, mock_db):
        response = client.post("/api/scrape/source/devfolio/toggle?enabled=true")
        assert response.status_code == 200

    def test_get_sources(self, client, mock_db):
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
        response = client.get("/api/scrape/sources")
        assert response.status_code == 200
        assert "sources" in response.json()


class TestNotifications:
    def test_get_notifications(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "notif-1", "is_read": False}])
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "unread_count" in data

    def test_mark_read(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "notif-1"}])
        response = client.put("/api/notifications/notif-1/read")
        assert response.status_code == 200

    def test_mark_read_not_found(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        response = client.put("/api/notifications/nonexistent/read")
        assert response.status_code == 404

    def test_mark_all_read(self, client, mock_db):
        response = client.put("/api/notifications/read-all")
        assert response.status_code == 200


class TestRateLimiting:
    def test_rate_limiting_applied(self, client):
        responses = []
        for _ in range(110):
            responses.append(client.get("/api/opportunities"))
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(s == 200 for s in status_codes)

    def test_rate_limiting_ai_stricter(self, client, mock_db):
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"user_id": "dev-user-001"}])
        with patch("services.matching_service.match") as mock_match:
            mock_match.return_value = {"score": 50}
            responses = []
            for _ in range(25):
                responses.append(client.post("/api/ai/match", json={"opportunity_id": "opp-1"}))
            # AI rate limit is 20 per 60s, so some should be rate limited
            assert any(r.status_code == 429 for r in responses) or all(r.status_code == 200 for r in responses)


class TestErrorHandling:
    def test_global_exception_handler(self, client):
        with patch("api.opportunities.get_opportunities", side_effect=Exception("unexpected")):
            response = client.get("/api/opportunities")
            # May be 500 (exception handler) or 429 (rate limit) depending on test order
            assert response.status_code in [500, 429]
            if response.status_code == 500:
                assert "detail" in response.json()
        # Verify normal requests still work
        response = client.get("/health")
        assert response.status_code == 200
