import pytest

from app import database
from app.agent_pipeline.evidence_judge import validate_decisions
from app.agent_pipeline.jd_extractor import validate_requirement_quotes
from app.agent_pipeline.orchestrator import run_analysis_pipeline
from app.agent_pipeline.scorer import score_requirements
from app.config import settings
from app.schemas.agent_pipeline import (
    EvidenceCandidate,
    EvidenceDecision,
    JDRequirement,
)


def _requirement() -> JDRequirement:
    return JDRequirement(
        id="req-1",
        text="Python",
        skill="Python",
        category="must",
        weight=2,
        source_quote="要求 Python",
    )


def test_jd_source_quote_must_be_in_original_text():
    with pytest.raises(ValueError, match="source_quote"):
        validate_requirement_quotes([_requirement()], "岗位要求 Java")


def test_supported_requires_real_evidence_id():
    with pytest.raises(ValueError, match="evidence_id"):
        EvidenceDecision(
            requirement_id="req-1",
            status="supported",
            evidence_ids=[],
            confidence=0.9,
            rationale="看起来匹配",
        )


def test_decision_rejects_unknown_evidence_id():
    requirement = _requirement()
    candidate = EvidenceCandidate(
        id="evidence-1",
        requirement_id="req-1",
        chunk_id="resume-1",
        snippet="项目中使用 Python",
        lexical_score=0.8,
    )
    decision = EvidenceDecision(
        requirement_id="req-1",
        status="supported",
        evidence_ids=["does-not-exist"],
        confidence=0.9,
        rationale="有证据",
    )
    with pytest.raises(ValueError, match="不存在"):
        validate_decisions([requirement], {"req-1": [candidate]}, [decision])


def test_score_is_deterministic_and_model_cannot_choose_total():
    requirement = _requirement()
    decision = EvidenceDecision(
        requirement_id="req-1",
        status="supported",
        evidence_ids=["evidence-1"],
        confidence=0.9,
        rationale="项目中有 Python",
    )
    result = score_requirements([requirement], [decision], "项目经历：Python 后端服务")
    assert result.score == 85
    assert result.must_coverage == 1
    assert result.project_relevance == 1


def test_pipeline_falls_back_when_llm_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "pipeline.db")
    monkeypatch.setattr(settings, "deepseek_api_key", None)
    database.init_db()
    session = database.create_copilot_session(None, "Python 后端开发实习")
    created = database.create_copilot_message_and_turn(
        session["id"], "岗位要求 Python、FastAPI，负责后端接口开发和项目维护。" * 4
    )
    assert created is not None
    _, turn = created

    result = run_analysis_pipeline(
        turn_id=turn["id"],
        resume_text="项目经历：使用 Python 和 FastAPI 开发后端服务，完成接口设计。" * 3,
        jd_text="岗位要求 Python、FastAPI，负责后端接口开发和项目维护。" * 4,
        target_role="Python 后端开发实习",
        use_llm=True,
    )

    assert result.degraded is True
    assert result.analysis.score >= 0
    runs = database.list_analysis_runs(turn["id"])
    assert runs and runs[0]["status"] == "degraded"
    stages = database.list_agent_stage_runs(runs[0]["id"])
    assert {item["stage"] for item in stages} >= {
        "queued",
        "jd_extracted",
        "evidence_retrieved",
        "evidence_judged",
        "scored",
        "report_generated",
    }
    with database.sqlite3.connect(database.DB_PATH) as conn:
        evidence_count = conn.execute(
            "SELECT COUNT(*) FROM requirement_evidence WHERE analysis_run_id = ?",
            (runs[0]["id"],),
        ).fetchone()[0]
    assert evidence_count == len(result.requirements)

