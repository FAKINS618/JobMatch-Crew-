import json

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app import database
from app.api.health import readiness
from app.config import settings
from app.main import app


def test_readiness_checks_required_sqlite_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ready.db")
    database.init_db()
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database_ready": True}


def test_readiness_hides_database_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "empty.db")
    with pytest.raises(HTTPException) as error:
        readiness()
    assert error.value.status_code == 503
    assert "sqlite" not in str(error.value.detail).lower()


def test_capabilities_are_non_sensitive():
    response = TestClient(app).get("/api/v1/system/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["storage_mode"] == "local_sqlite"
    assert payload["evidence_feedback_enabled"] is True
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    assert "api_key" not in serialized
    assert "base_url" not in serialized
    assert "resume_text" not in serialized
    assert "jd_text" not in serialized


def test_sse_emits_keepalive_and_preserves_turn_events(monkeypatch):
    turns = iter(
        [
            {"id": 1, "status": "running", "progress": 20},
            {"id": 1, "status": "completed", "progress": 100},
        ]
    )
    monkeypatch.setattr(
        "app.api.copilot.get_copilot_turn", lambda _turn_id: next(turns)
    )
    monkeypatch.setattr(settings, "sse_max_seconds", 5)
    monkeypatch.setattr(settings, "sse_poll_interval_seconds", 0.1)

    response = TestClient(app).get("/api/v1/copilot/turns/1/events")
    assert response.status_code == 200
    assert "event: turn" in response.text
    assert ": keepalive" in response.text
    assert "event: timeout" not in response.text
