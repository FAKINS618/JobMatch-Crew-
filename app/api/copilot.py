"""Vue 求职副驾的会话、分析回合和 SSE 事件接口。"""

import asyncio
import json
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from app.database import (
    create_artifact_decision,
    create_copilot_message_and_turn,
    create_copilot_session,
    create_evidence_feedback,
    get_analysis_evidence_chain,
    get_copilot_session,
    get_copilot_turn,
)
from app.schemas import (
    AnalysisTurnResponse,
    ArtifactDecisionCreate,
    ArtifactDecisionResponse,
    CopilotMessageCreate,
    CopilotSessionCreate,
    CopilotSessionDetailResponse,
    CopilotSessionResponse,
)
from app.schemas.agent_pipeline import (
    EvidenceChainResponse,
    EvidenceFeedback,
    EvidenceFeedbackRequest,
)
from app.config import settings
from app.services.copilot_service import run_copilot_turn


router = APIRouter(prefix="/api/v1/copilot", tags=["Copilot"])


@router.post("/sessions", response_model=CopilotSessionResponse, status_code=201)
def create_session(payload: CopilotSessionCreate) -> CopilotSessionResponse:
    try:
        session = create_copilot_session(payload.resume_version_id, payload.target_role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CopilotSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}", response_model=CopilotSessionDetailResponse)
def get_session(session_id: int) -> CopilotSessionDetailResponse:
    session = get_copilot_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="副驾会话不存在")
    return CopilotSessionDetailResponse.model_validate(session)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AnalysisTurnResponse,
    status_code=202,
)
def send_message(
    session_id: int,
    payload: CopilotMessageCreate,
    background_tasks: BackgroundTasks,
) -> AnalysisTurnResponse:
    created = create_copilot_message_and_turn(session_id, payload.content)
    if created is None:
        raise HTTPException(status_code=404, detail="副驾会话不存在")
    _, turn = created
    background_tasks.add_task(run_copilot_turn, int(turn["id"]))
    return AnalysisTurnResponse.model_validate(turn)


@router.get("/turns/{turn_id}", response_model=AnalysisTurnResponse)
def get_turn(turn_id: int) -> AnalysisTurnResponse:
    turn = get_copilot_turn(turn_id)
    if turn is None:
        raise HTTPException(status_code=404, detail="分析回合不存在")
    return AnalysisTurnResponse.model_validate(turn)


@router.get("/turns/{turn_id}/evidence", response_model=EvidenceChainResponse)
def get_turn_evidence(turn_id: int) -> EvidenceChainResponse:
    """Return structured requirement evidence without raw prompts or resume text."""
    if get_copilot_turn(turn_id) is None:
        raise HTTPException(status_code=404, detail="分析回合不存在")
    evidence = get_analysis_evidence_chain(turn_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="证据链不存在")
    return EvidenceChainResponse.model_validate({"turn_id": turn_id, **evidence})


@router.post(
    "/turns/{turn_id}/evidence-feedback",
    response_model=EvidenceFeedback,
    status_code=201,
)
def submit_evidence_feedback(
    turn_id: int, payload: EvidenceFeedbackRequest
) -> EvidenceFeedback:
    if get_copilot_turn(turn_id) is None:
        raise HTTPException(status_code=404, detail="分析回合不存在")
    evidence = get_analysis_evidence_chain(turn_id)
    if evidence is None or not evidence.get("items"):
        raise HTTPException(status_code=409, detail="证据链尚未生成")
    item = next(
        (
            value
            for value in evidence["items"]
            if value.get("requirement", {}).get("id") == payload.requirement_id
        ),
        None,
    )
    if item is None:
        raise HTTPException(status_code=422, detail="requirement 不存在")
    candidate_map = {
        candidate.get("id"): candidate
        for candidate in item.get("candidates", [])
        if isinstance(candidate, dict)
    }
    if any(
        evidence_id not in candidate_map
        or candidate_map[evidence_id].get("requirement_id") != payload.requirement_id
        for evidence_id in payload.evidence_ids
    ):
        raise HTTPException(status_code=422, detail="evidence_id 不属于该 requirement")
    try:
        created = create_evidence_feedback(
            turn_id=turn_id,
            analysis_run_id=int(evidence["analysis_run_id"]),
            requirement_id=payload.requirement_id,
            verdict=payload.verdict,
            corrected_status=payload.corrected_status,
            evidence_ids=payload.evidence_ids,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EvidenceFeedback.model_validate(created)


@router.get("/turns/{turn_id}/events")
async def stream_turn_events(turn_id: int) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        previous_payload = ""
        started_at = time.monotonic()
        while time.monotonic() - started_at < max(1, settings.sse_max_seconds):
            turn = get_copilot_turn(turn_id)
            if turn is None:
                yield "event: error\ndata: {\"message\": \"分析回合不存在\"}\n\n"
                return
            payload = json.dumps(turn, ensure_ascii=False, default=str)
            if payload != previous_payload:
                yield f"event: turn\ndata: {payload}\n\n"
                previous_payload = payload
            if turn["status"] in {"completed", "failed"}:
                return
            yield ": keepalive\n\n"
            await asyncio.sleep(max(0.1, settings.sse_poll_interval_seconds))
        yield "event: timeout\ndata: {\"message\": \"分析仍在运行，请稍后查询分析回合。\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/artifacts/{artifact_id}/decisions",
    response_model=ArtifactDecisionResponse,
    status_code=201,
)
def decide_artifact(
    artifact_id: int, payload: ArtifactDecisionCreate
) -> ArtifactDecisionResponse:
    decision = create_artifact_decision(artifact_id, payload.decision, payload.note)
    if decision is None:
        raise HTTPException(status_code=404, detail="分析产物不存在")
    return ArtifactDecisionResponse.model_validate(decision)
