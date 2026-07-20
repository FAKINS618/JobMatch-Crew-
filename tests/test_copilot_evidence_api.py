import json

from fastapi.testclient import TestClient

from app import database
from app.agent_pipeline.orchestrator import run_analysis_pipeline
from app.main import app


def test_evidence_api_returns_structured_chain_without_raw_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "evidence-api.db")
    database.init_db()
    session = database.create_copilot_session(None, "Python 后端开发实习")
    created = database.create_copilot_message_and_turn(
        session["id"], "岗位要求 Python、FastAPI，负责项目接口开发和维护。" * 4
    )
    assert created is not None
    _, turn = created
    run_analysis_pipeline(
        turn_id=turn["id"],
        resume_text="项目经历：使用 Python 和 FastAPI 开发后端接口。" * 3,
        jd_text="岗位要求 Python、FastAPI，负责项目接口开发和维护。" * 4,
        target_role="Python 后端开发实习",
        use_llm=False,
    )

    response = TestClient(app).get(f"/api/v1/copilot/turns/{turn['id']}/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["turn_id"] == turn["id"]
    assert payload["items"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "raw_output" not in serialized
    assert "resume_text" not in serialized
    assert "jd_text" not in serialized
    assert payload["items"][0]["candidates"][0]["chunk_id"] in {
        chunk["id"] for chunk in payload["items"][0]["chunks"]
    }


def test_evidence_api_returns_404_for_unknown_turn(monkeypatch):
    monkeypatch.setattr("app.api.copilot.get_copilot_turn", lambda _turn_id: None)

    response = TestClient(app).get("/api/v1/copilot/turns/999999/evidence")

    assert response.status_code == 404
