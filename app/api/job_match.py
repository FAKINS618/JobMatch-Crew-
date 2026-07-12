import logging

from fastapi import APIRouter, HTTPException
from app.schemas import JobMatchRequest, JobMatchResponse
from app.services.jobmatch_service import generate_job_match_report


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Job Match"])


@router.post("/job-match", response_model=JobMatchResponse)
def create_job_match_report(payload: JobMatchRequest) -> JobMatchResponse:
    """
        生成简历和岗位 JD 的匹配分析报告。
        定义 POST /api/job-match
        请求体必须符合 JobMatchRequest
        返回体必须符合 JobMatchResponse
        真正业务交给 generate_job_match_report
        出错时返回 500

    """
    try:
        return generate_job_match_report(payload)
    except Exception:
        logger.exception("Job match report generation failed")
        raise HTTPException(status_code=500, detail="报告生成失败，请稍后重试")
