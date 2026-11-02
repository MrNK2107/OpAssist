"""Tests for the public landing-page stats endpoint."""
from unittest.mock import MagicMock

import pytest

from api import opportunities as opp_api


@pytest.fixture(autouse=True)
def _clear_stats_cache():
    # Earlier test modules can exhaust the in-memory per-IP rate limit.
    import main

    main._rate_limit_store.clear()
    opp_api._reset_stats_cache()
    yield
    opp_api._reset_stats_cache()


def _wire_counts(mock_db, counts: dict[str, int]):
    """Make select(...).eq("type", t).execute() return counts[t]."""
    select = mock_db.table.return_value.select

    def eq(field, value):
        assert field == "type"
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=[], count=counts.get(value, 0))
        return chain

    select.return_value.eq.side_effect = eq
    return select


def test_stats_counts_per_type(client, mock_db):
    select = _wire_counts(mock_db, {"hackathon": 12, "job": 40, "internship": 7})
    r = client.get("/api/opportunities/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert body["by_type"]["hackathon"] == 12
    assert body["by_type"]["job"] == 40
    assert body["by_type"]["scholarship"] == 0
    assert body["total"] == 59
    # head-only count queries: no rows are transferred
    _, kwargs = select.call_args
    assert kwargs == {"count": "exact", "head": True}


def test_stats_route_not_shadowed_by_id_route(client, mock_db):
    _wire_counts(mock_db, {})
    r = client.get("/api/opportunities/stats")
    assert r.status_code == 200
    assert set(r.json()) == {"by_type", "total", "available"}


def test_stats_covers_every_opportunity_type(client, mock_db):
    from models.schemas import OpportunityType

    _wire_counts(mock_db, {})
    body = client.get("/api/opportunities/stats").json()
    assert set(body["by_type"]) == {t.value for t in OpportunityType}


def test_stats_unavailable_on_db_error(client, mock_db):
    mock_db.table.return_value.select.return_value.eq.side_effect = RuntimeError("down")
    body = client.get("/api/opportunities/stats").json()
    assert body["available"] is False
    assert body["total"] == 0


def test_stats_unavailable_without_db(client, mock_db):
    original = opp_api.db
    opp_api.db = MagicMock(client=None)
    try:
        body = client.get("/api/opportunities/stats").json()
    finally:
        opp_api.db = original
    assert body["available"] is False


def test_stats_are_cached(client, mock_db):
    select = _wire_counts(mock_db, {"job": 3})
    client.get("/api/opportunities/stats")
    calls = select.return_value.eq.call_count
    body = client.get("/api/opportunities/stats").json()
    assert select.return_value.eq.call_count == calls
    assert body["by_type"]["job"] == 3


def test_stats_errors_are_not_cached(client, mock_db):
    select = mock_db.table.return_value.select
    select.return_value.eq.side_effect = RuntimeError("down")
    assert client.get("/api/opportunities/stats").json()["available"] is False
    _wire_counts(mock_db, {"job": 5})
    body = client.get("/api/opportunities/stats").json()
    assert body["available"] is True
    assert body["total"] == 5
