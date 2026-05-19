import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.auth = MagicMock()
    mock.auth.get_user.return_value = MagicMock(user=MagicMock(id="test-user-id"))
    return mock


@pytest.fixture
def mock_db(mock_supabase, monkeypatch):
    """Patch the database client for testing."""
    from database import supabase_client
    monkeypatch.setattr(supabase_client, "db", MagicMock(client=mock_supabase, admin=mock_supabase))
    return mock_supabase


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
    # Set ALLOW_DEV_AUTH for testing
    import os
    os.environ["ALLOW_DEV_AUTH"] = "true"

    from main import app
    return TestClient(app)


@pytest.fixture
def sample_opportunity():
    """Sample opportunity data for testing."""
    return {
        "id": "opp-123",
        "title": "Test Hackathon",
        "type": "hackathon",
        "description": "A test hackathon event",
        "organizer": "Test Org",
        "deadline": "2026-06-01",
        "location": "Online",
        "prize": "$1000",
        "tags": ["python", "ai"],
        "difficulty": "beginner",
        "is_closed": False,
        "url": "https://example.com/hackathon",
        "source": "test",
    }


@pytest.fixture
def sample_profile():
    """Sample user profile for testing."""
    return {
        "user_id": "test-user-id",
        "name": "Test User",
        "university": "IIT Delhi",
        "year": 3,
        "skills": ["python", "react", "machine learning"],
        "interests": ["hackathons", "open source"],
        "bio": "Test bio",
    }
