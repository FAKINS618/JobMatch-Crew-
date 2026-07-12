import json
from pathlib import Path
from typing import Any

# 读取文件：[app/data/role_skill_map.json](E:\\py_project\\CrewAI\\jobmatch-crew\\app\\data\\role_skill_map.json)
# 前端显示岗位方向
# 快速检查简历中出现了哪些核心技能
# Agent 分析 JD 时作为参考
DATA_PATH = Path(__file__).resolve().parent / "data" / "role_skill_map.json"


def load_role_skill_map() -> dict[str, dict[str, Any]]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))

# 返回所有岗位方向
def list_roles() -> list[str]:
    return list(load_role_skill_map().keys())

# 返回某个岗位的技能图谱
def get_role_detail(role_name: str) -> dict[str, Any] | None:
    return load_role_skill_map().get(role_name)

# 把 JSON 技能图谱转成 Prompt 文本给大模型看
def format_role_skill_map_for_prompt() -> str:
    role_map = load_role_skill_map()
    sections = []

    for role, info in role_map.items():
        sections.append(
            f"""## {role}

核心技能：{", ".join(info.get("core_skills", []))}
项目关键词：{", ".join(info.get("project_keywords", []))}
学习优先级：{", ".join(info.get("learning_priority", []))}
"""
        )

    return "\n".join(sections)