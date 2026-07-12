import logging

from fastapi import APIRouter, HTTPException

from app.schemas import JobSearchRequest, JobSearchResponse
from app.search_service import search_jobs


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Job Search"])


@router.post("/search", response_model=JobSearchResponse)
def search_job_posts(payload: JobSearchRequest) -> JobSearchResponse:
    """联网搜索岗位信息，用于补充真实市场需求。"""
    query = f"{payload.keyword} 实习 招聘 {payload.city}".strip()

    try:
        results = search_jobs(query=query, max_results=payload.max_results)
        return JobSearchResponse(results=results)
    except Exception:
        logger.exception("Job search failed")
        raise HTTPException(status_code=500, detail="岗位搜索失败，请稍后重试")
