"""分析建议到行动任务、成果证据的接口。"""

from fastapi import APIRouter, HTTPException, Query

from app.database import (
    create_action_evidence,
    create_action_items_from_report,
    list_action_items,
    update_action_item,
)
from app.schemas import (
    ActionEvidenceCreate,
    ActionEvidenceResponse,
    ActionItemResponse,
    ActionItemsFromReportRequest,
    ActionItemUpdate,
)


router = APIRouter(prefix="/api/action-items", tags=["Action Items"])


@router.post("/from-report/{report_id}", response_model=list[ActionItemResponse], status_code=201)
def create_items_from_report(
    report_id: int, payload: ActionItemsFromReportRequest
) -> list[ActionItemResponse]:
    try:
        items = create_action_items_from_report(report_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [ActionItemResponse.model_validate(item) for item in items]


@router.get("", response_model=list[ActionItemResponse])
def get_action_items(status: str | None = Query(default=None)) -> list[ActionItemResponse]:
    return [ActionItemResponse.model_validate(item) for item in list_action_items(status)]


@router.patch("/{item_id}", response_model=ActionItemResponse)
def patch_action_item(item_id: int, payload: ActionItemUpdate) -> ActionItemResponse:
    try:
        item = update_action_item(item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="行动任务不存在")
    return ActionItemResponse.model_validate(item)


@router.post("/{item_id}/evidence", response_model=ActionEvidenceResponse, status_code=201)
def add_action_evidence(
    item_id: int, payload: ActionEvidenceCreate
) -> ActionEvidenceResponse:
    try:
        evidence = create_action_evidence(item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if evidence is None:
        raise HTTPException(status_code=404, detail="行动任务不存在")
    return ActionEvidenceResponse.model_validate(evidence)
