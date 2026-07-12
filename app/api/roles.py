from fastapi import APIRouter, HTTPException

from app.role_skill_repository import (
    get_role_detail as load_role_detail,
    list_roles,
)


router = APIRouter(prefix="/api", tags=["Roles"])


@router.get("/roles")
def get_roles() -> dict[str, list[str]]:
    """获取系统支持的岗位方向。"""
    return {"roles": list_roles()}


@router.get("/role-detail")
def get_role_detail_by_query(role_name: str) -> dict:
    """通过 query 参数读取岗位技能图谱，避免中文路径编码问题。"""
    role = load_role_detail(role_name)

    if role is None:
        raise HTTPException(status_code=404, detail="岗位方向不存在")

    return role


@router.get("/roles/{role_name}")
def get_role_detail_by_path(role_name: str) -> dict:
    """兼容旧版前端的岗位详情接口。"""
    role = load_role_detail(role_name)

    if role is None:
        raise HTTPException(status_code=404, detail="岗位方向不存在")

    return role
