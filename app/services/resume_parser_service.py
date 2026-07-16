from crewai import Agent, Crew, Process, Task
from pydantic import ValidationError

from app.llm_factory import build_llm
from app.prompt_loader import load_prompt
from app.report_parser import extract_json_block
from app.schemas import ResumeProfile


def _as_string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_resume_profile_payload(payload: dict) -> dict:
    """兼容模型的轻微字段形状偏差，不推测或补造简历事实。"""
    normalized = dict(payload)
    for field in (
        "education",
        "skills",
        "internships",
        "awards",
        "target_roles",
        "parse_notes",
    ):
        normalized[field] = _as_string_list(normalized.get(field, []))

    projects = normalized.get("projects", [])
    if not isinstance(projects, list):
        projects = []
    normalized_projects = []
    for project in projects:
        if isinstance(project, str) and project.strip():
            normalized_projects.append({"name": project.strip()})
            continue
        if not isinstance(project, dict):
            continue
        name = project.get("name") or project.get("title") or project.get("project_name")
        if not isinstance(name, str) or not name.strip():
            continue
        normalized_projects.append(
            {
                "name": name.strip(),
                "role": str(project.get("role") or "").strip(),
                "technologies": _as_string_list(project.get("technologies", [])),
                "description": str(project.get("description") or "").strip(),
                "achievements": _as_string_list(project.get("achievements", [])),
            }
        )
    normalized["projects"] = normalized_projects
    normalized["available_from"] = str(normalized.get("available_from") or "").strip()
    return normalized


def call_resume_parser_llm(raw_text: str) -> str:
    """调用模型，将原始简历转换为 ResumeProfile JSON。"""
    parser_agent = Agent(
        role="简历结构化解析助手",
        goal="从简历中提取真实存在的信息，不能补造经历。",
        backstory=load_prompt("resume_parser.md"),
        # 简历提取是信息还原任务，温度设为 0 可降低同一输入多次解析不一致的概率。
        llm=build_llm(temperature=0),
        verbose=False,
    )

    task = Task(
        description=f"""
候选人简历如下：

{raw_text}

请只输出符合 ResumeProfile 的 JSON。
        """,
        expected_output="合法的 ResumeProfile JSON，不要输出 Markdown 代码块。",
        agent=parser_agent,
    )

    crew = Crew(
        agents=[parser_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    return str(crew.kickoff())


def parse_resume_to_profile(raw_text: str) -> ResumeProfile:
    raw_result = call_resume_parser_llm(raw_text)
    parsed = extract_json_block(raw_result)

    if not parsed:
        raise ValueError("简历结构化解析失败，请手动补充信息后重试")

    try:
        return ResumeProfile.model_validate(normalize_resume_profile_payload(parsed))
    except ValidationError as exc:
        raise ValueError(f"简历结构化字段校验失败：{exc}") from exc
