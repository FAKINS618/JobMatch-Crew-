from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database import create_analysis_task, get_analysis_task
from app.schemas import MarketMatchRequest
from app.services.analysis_task_service import run_market_match_task


router = APIRouter(prefix="/api/tasks",tags=["Analysis Tasks"])
@router.post("/market-match")
def create_market_match_task(
    payload: MarketMatchRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """创建岗位市场匹配异步任务。"""
    task_id = create_analysis_task(task_type="market_match")
    background_tasks.add_task(run_market_match_task, task_id, payload)

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
def get_task_detail(task_id: int) -> dict:
    """查询异步任务状态。"""
    task = get_analysis_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task