from fastapi import APIRouter, HTTPException
from app.schemas import (
    ResumeAnalysisHistoryResponse,
    ResumeMarketSearchPreference,
    ResumeMarketSearchPreferenceUpdate,
    ResumeParseRequest,
    ResumeParseResponse,
    ResumeVersionCreate,
    ResumeVersionResponse,
)
from app.services.resume_parser_service import parse_resume_to_profile
from app.database import (
    create_resume_version,
    get_resume_analysis_history,
    get_resume_market_search_preference,
    list_resume_versions,
    update_resume_market_search_preference,
)

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/parse", response_model=ResumeParseResponse)
def parse_resume(payload: ResumeParseRequest) -> ResumeParseResponse:
    """将原始简历解析为可由用户确认的结构化档案。"""
    try:
        profile = parse_resume_to_profile(payload.raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ResumeParseResponse(profile=profile)


@router.post("/versions", response_model=ResumeVersionResponse)
def save_resume_version(payload: ResumeVersionCreate) -> ResumeVersionResponse:
    try:
        saved_version = create_resume_version(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ResumeVersionResponse.model_validate(saved_version)


@router.get("/versions", response_model=list[ResumeVersionResponse])
def get_resume_versions() -> list[ResumeVersionResponse]:
    """返回已保存的简历版本，供工作台选择。"""
    return [
        ResumeVersionResponse.model_validate(item)
        for item in list_resume_versions()
    ]


@router.get(
    "/versions/{resume_version_id}/history",
    response_model=ResumeAnalysisHistoryResponse,
)
def get_resume_history(resume_version_id: int) -> ResumeAnalysisHistoryResponse:
    history = get_resume_analysis_history(resume_version_id)
    if history is None:
        raise HTTPException(status_code=404, detail="简历版本不存在")
    return ResumeAnalysisHistoryResponse.model_validate(history)


@router.get(
    "/versions/{resume_version_id}/market-search-preference",
    response_model=ResumeMarketSearchPreference,
)
def get_market_search_preference(resume_version_id: int) -> ResumeMarketSearchPreference:
    preference = get_resume_market_search_preference(resume_version_id)
    if preference is None:
        raise HTTPException(status_code=404, detail="简历版本不存在")
    return ResumeMarketSearchPreference.model_validate(preference)


@router.patch(
    "/versions/{resume_version_id}/market-search-preference",
    response_model=ResumeMarketSearchPreference,
)
def patch_market_search_preference(
    resume_version_id: int, payload: ResumeMarketSearchPreferenceUpdate
) -> ResumeMarketSearchPreference:
    try:
        preference = update_resume_market_search_preference(
            resume_version_id,
            auto_search_enabled=payload.auto_search_enabled,
            city=payload.city,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResumeMarketSearchPreference.model_validate(preference)
