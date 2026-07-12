from fastapi import APIRouter, HTTPException

from app.database import get_report, list_job_posts, list_reports


router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("")
def get_reports() -> dict[str, list[dict]]:
    """获取历史报告摘要列表。"""
    return {"reports": list_reports()}


@router.get("/{report_id}")
def get_report_detail(report_id: int) -> dict:
    """根据报告 ID 获取完整报告内容。"""
    report = get_report(report_id)

    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 市场匹配报告会额外保存岗位样本；普通 JD 匹配报告这里会返回空列表。
    report["job_posts"] = list_job_posts(report_id)

    return report
