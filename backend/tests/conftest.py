import os

# Set environment BEFORE any imports that might read settings
os.environ.setdefault("ALLOW_DEV_AUTH", "true")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("FIREBASE_PRIVATE_KEY_ID", "test-key-id")
os.environ.setdefault("FIREBASE_PRIVATE_KEY", "test-key")
os.environ.setdefault("FIREBASE_CLIENT_EMAIL", "test@test.com")
os.environ.setdefault("FIREBASE_CLIENT_ID", "test-client-id")

# Clear any cached settings
from config import get_settings as _get_settings
_get_settings.cache_clear()

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_settings():
    _get_settings.cache_clear()
    yield


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[], count=0)
    mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id", "status": "saved"}])
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    mock.auth = MagicMock()
    mock.auth.get_user.return_value = MagicMock(user=MagicMock(id="test-user-id"))
    # Support order and range chaining
    mock.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.select.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    # .not_ and .is_ chains
    mock.table.return_value.select.return_value.not_.is_.return_value.lt.return_value.execute.return_value = MagicMock(data=[], count=0)
    # gte/lte chains
    mock.table.return_value.select.return_value.gte.return_value.lte.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(data=[])
    # range chain
    mock.table.return_value.select.return_value.range.return_value.execute.return_value = MagicMock(data=[], count=0)
    # .or_ chain
    mock.table.return_value.select.return_value.or_.return_value.range.return_value.execute.return_value = MagicMock(data=[], count=0)
    # ilike chain
    mock.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    mock.table.return_value.select.return_value.ilike.return_value.execute.return_value = MagicMock(data=[])
    # in_ for profile batch fetch
    mock.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
    return mock


@pytest.fixture
def mock_db(mock_supabase):
    """Patch the database client for all API module imports."""
    from database import supabase_client
    # Need to also patch individual modules that imported 'db'
    from api import opportunities, profiles, bookmarks, applications, ai, communities, scraping, notifications
    from services import scraper_service, notification_service
    from scheduler import jobs

    mock_db_obj = MagicMock(client=mock_supabase, admin=mock_supabase)

    for mod in [supabase_client, opportunities, profiles, bookmarks, applications,
                ai, communities, scraping, notifications,
                scraper_service, notification_service, jobs]:
        mod.db = mock_db_obj

    return mock_supabase


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
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
