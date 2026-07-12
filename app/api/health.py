from fastapi import APIRouter


router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict[str, str]:
    """服务健康检查，用于确认后端是否启动成功。"""
    return {"status": "ok"}
