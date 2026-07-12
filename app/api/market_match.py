import logging

from fastapi import APIRouter, HTTPException

from app.schemas import MarketMatchRequest, MarketMatchResponse
from app.services.market_match_service import generate_market_match_report


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Market Match"])


@router.post("/market-match", response_model=MarketMatchResponse)
def create_market_match_report(payload: MarketMatchRequest) -> MarketMatchResponse:
    """根据简历和目标方向，自动搜索岗位并生成市场匹配分析。"""
    try:
        return generate_market_match_report(payload)
    except Exception:
        logger.exception("Market match report generation failed")
        raise HTTPException(status_code=500, detail="岗位市场匹配分析失败")