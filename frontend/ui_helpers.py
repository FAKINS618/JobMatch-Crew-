from typing import Any


def split_matched_skills(
    resume_text: str,
    skills: list[str],
) -> tuple[list[str], list[str]]:
    """用关键词快速判断简历是否覆盖岗位核心技能。"""
    matched = []
    missing = []
    lower_resume = resume_text.lower()

    for skill in skills:
        if skill.lower() in lower_resume:
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def format_tags(items: list[str]) -> str:
    """把技能列表渲染成 Streamlit 友好的 Markdown 标签。"""
    if not items:
        return "暂无"
    return " ".join(f"`{item}`" for item in items)


def get_role_core_skills(role_info: dict[str, Any]) -> list[str]:
    """安全读取岗位技能图谱中的核心技能。"""
    skills = role_info.get("core_skills", [])
    if not isinstance(skills, list):
        return []
    return [str(skill) for skill in skills]
