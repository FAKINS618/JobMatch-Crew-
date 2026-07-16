from fastapi import APIRouter, HTTPException
from app.schemas import (
    ResumeParseRequest,
    ResumeParseResponse,
    ResumeVersionCreate,
    ResumeVersionResponse,
)
from app.services.resume_parser_service import parse_resume_to_profile
from app.database import create_resume_version, list_resume_versions

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
