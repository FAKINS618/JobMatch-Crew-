from typing import Any
from config import API_BASE_URL
import requests



def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    """统一处理前端到 FastAPI 的请求和错误。

    前端页面不直接拼接后端细节，所有接口调用都集中在这个文件。
    """
    response = requests.request(method, f"{API_BASE_URL}{path}", **kwargs)
    response.raise_for_status()
    return response.json()


def fetch_roles() -> list[str]:
    """读取后端支持的岗位方向列表。"""
    data = _request("GET", "/api/roles", timeout=10)
    return data.get("roles", [])


def fetch_role_detail(role_name: str) -> dict[str, Any]:
    """读取某个岗位方向的技能图谱。"""
    return _request(
        "GET",
        "/api/role-detail",
        params={"role_name": role_name},
        timeout=10,
    )


def create_job_match_report(payload: dict[str, Any]) -> dict[str, Any]:
    """提交简历和 JD，生成求职匹配报告。"""
    return _request("POST", "/api/job-match", json=payload, timeout=180)


def search_jobs(payload: dict[str, Any]) -> dict[str, Any]:
    """联网搜索岗位信息。"""
    return _request("POST", "/api/jobs/search", json=payload, timeout=60)


def list_reports() -> dict[str, Any]:
    """获取历史报告列表。"""
    return _request("GET", "/api/reports", timeout=30)


def get_report_detail(report_id: int) -> dict[str, Any]:
    """根据报告 ID 获取完整历史报告。"""
    return _request("GET", f"/api/reports/{report_id}", timeout=30)

def create_market_match_report(payload: dict[str, Any]) -> dict[str, Any]:
    """提交简历和目标方向，生成岗位市场匹配分析。"""
    return _request("POST", "/api/market-match", json=payload, timeout=180)

def create_market_match_task(payload: dict[str, Any]) -> dict[str, Any]:
    """创建岗位市场匹配异步任务。"""
    return _request("POST", "/api/tasks/market-match", json=payload, timeout=30)

def get_task_detail(task_id: int) -> dict[str, Any]:
    """查询异步任务状态。"""
    return _request("GET", f"/api/tasks/{task_id}", timeout=10)