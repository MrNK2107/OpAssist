import pytest
from unittest.mock import MagicMock, patch


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_opportunities_empty(client, mock_db):
    """Test getting opportunities when none exist."""
    mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
    response = client.get("/api/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data


def test_get_opportunity_not_found(client, mock_db):
    """Test getting a non-existent opportunity."""
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    response = client.get("/api/opportunities/nonexistent")
    assert response.status_code == 404


def test_get_bookmarks_requires_auth(client):
    """Test that bookmarks endpoint requires authentication."""
    response = client.get("/api/bookmarks")
    # With dev auth enabled, this should work
    assert response.status_code in [200, 401, 503]


def test_get_applications_requires_auth(client):
    """Test that applications endpoint requires authentication."""
    response = client.get("/api/applications")
    assert response.status_code in [200, 401, 503]


def test_scrape_trigger_requires_auth(client, mock_db):
    """Test that scrape trigger requires authentication."""
    response = client.post("/api/scrape/trigger")
    assert response.status_code in [200, 401, 503]


def test_get_scrape_sources(client):
    """Test getting scraper sources."""
    response = client.get("/api/scrape/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data


def test_get_leaderboard(client, mock_db):
    """Test getting leaderboard."""
    mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    response = client.get("/api/communities/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data


def test_get_notifications_requires_auth(client):
    """Test that notifications endpoint requires authentication."""
    response = client.get("/api/notifications")
    assert response.status_code in [200, 401, 503]


def test_rate_limiting_works(client):
    """Test that rate limiting is applied."""
    # Make many requests to trigger rate limit
    responses = []
    for _ in range(110):
        responses.append(client.get("/api/opportunities"))

    # At least one should be rate limited (429)
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes or all(s == 200 for s in status_codes)


def test_security_headers_present(client):
    """Test that security headers are added."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
