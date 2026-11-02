"""ALLOW_DEV_AUTH must never hand out the mock user when ENV=production."""

import asyncio

import pytest
from fastapi import HTTPException

import api.deps as deps
from config import Settings


def _call(monkeypatch, **env):
    monkeypatch.setattr(deps, "settings", Settings(_env_file=None, **env))
    monkeypatch.setattr(deps, "_get_firebase_app", lambda: None)  # Firebase not configured
    return asyncio.run(deps.get_current_user_id(credentials=None))


def test_dev_auth_works_outside_production(monkeypatch):
    assert _call(monkeypatch, allow_dev_auth=True, env="development") == "dev-user-001"


@pytest.mark.parametrize("env", ["production", "PRODUCTION", " Production "])
def test_dev_auth_is_refused_in_production(monkeypatch, env):
    with pytest.raises(HTTPException) as exc:
        _call(monkeypatch, allow_dev_auth=True, env=env)
    assert exc.value.status_code == 503


def test_settings_flag_reports_effective_dev_auth():
    assert Settings(_env_file=None, allow_dev_auth=True, env="development").dev_auth_enabled
    assert not Settings(_env_file=None, allow_dev_auth=True, env="production").dev_auth_enabled
    assert not Settings(_env_file=None, allow_dev_auth=False, env="development").dev_auth_enabled
