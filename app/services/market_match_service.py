import json
import logging

from crewai import Agent, Crew, LLM, Process, Task
from pydantic import ValidationError
from app.config import settings
from app.database import save_job_posts, save_report
from app.prompt_loader import load_prompt
from app.report_parser import extract_json_block
from app.schemas import (
    MarketMatchRequest,
    MarketMatchResponse,
    MarketResumeMatchAnalysis,
)
from app.services.market_profile_service import build_market_profile


logger = logging.getLogger(__name__)

# 市场匹配服务

def _build_llm() -> LLM:
    return LLM(
        model=settings.model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=120,
    )


def generate_market_match_report(payload: MarketMatchRequest) -> MarketMatchResponse:
    """基于真实岗位搜索结果，分析简历与目标方向市场需求的匹配度。"""
    market_profile, job_posts = build_market_profile(
        target_role=payload.target_role,
        city=payload.city,
        max_results=payload.max_results,
    )

    llm = _build_llm()

    analyst = Agent(
        role="计算机求职规划顾问",
        goal="根据简历和岗位市场画像分析求职匹配度，并给出投递建议",
        backstory=load_prompt("market_match_analyst.md"),
        llm=llm,
        verbose=True,
    )

    task = Task(
        description=f"""
        候选人简历：

        {payload.resume_text}

        岗位市场画像：

        {market_profile.model_dump_json(indent=2)}

        请输出 MarketResumeMatchAnalysis JSON。
        """,
        expected_output="符合 MarketResumeMatchAnalysis 结构的 JSON",
        agent=analyst,
    )

    crew = Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    raw_result = str(crew.kickoff())
    parsed = extract_json_block(raw_result)

    parse_status = "success"
    parse_error = None
    parsed_result = None

    # 市场匹配分析的稳定性兜底：
    # LLM 可能输出多余解释、字段类型错误或不完整 JSON，后端不能因为解析失败直接崩溃。
    if not parsed:
        logger.warning("Market match JSON parse failed")
        parse_status = "raw_only"
        parse_error = "未能从模型输出中解析 JSON"

        analysis = MarketResumeMatchAnalysis(
            score=0,
            summary="岗位市场匹配分析失败，未能从模型输出中解析结构化结果，请稍后重试或减少输入内容后再次分析。",
        )
    else:
        try:
            analysis = MarketResumeMatchAnalysis.model_validate(parsed)
            parsed_result = analysis.model_dump_json()
        except ValidationError as exc:
            logger.warning("Market match JSON validation failed: %s", exc)
            parse_status = "validation_failed"
            parse_error = str(exc)
            parsed_result = json.dumps(parsed, ensure_ascii=False)

            analysis = MarketResumeMatchAnalysis(
                score=0,
                summary="岗位市场匹配分析已完成，但模型输出字段不完全符合系统结构，当前展示降级后的结果。",
            )



    markdown_report = render_market_match_report(market_profile, analysis)

    # 市场匹配分析没有用户手动粘贴的 JD，这里把岗位画像 JSON 保存到 jd_text，
    # 方便历史报告仍然能追溯“这次分析基于什么市场数据”。
    report_id = save_report(
        target_role=payload.target_role,
        score=analysis.score,
        resume_text=payload.resume_text,
        jd_text=market_profile.model_dump_json(indent=2),
        markdown_report=markdown_report,
        raw_result=raw_result,
        parsed_result=parsed_result,
        parse_status=parse_status,
        parse_error=parse_error,
        model_name=settings.model,
    )
    save_job_posts(report_id=report_id, posts=job_posts)
    logger.info("Saved market match report id=%s with %s job posts", report_id, len(job_posts))

    return MarketMatchResponse(
        market_profile=market_profile,
        analysis=analysis,
        markdown_report=markdown_report,
        report_id=report_id,
    )


def render_market_match_report(
    market_profile,
    analysis: MarketResumeMatchAnalysis,
) -> str:
    lines = [
        "# 岗位市场匹配分析报告",
        "",
        f"## 目标方向：{market_profile.target_role}",
        "",
        f"样本岗位数量：{market_profile.sample_count}",
        "",
        f"市场匹配分：**{analysis.score}/100**",
        "",
        "## 匹配总览",
        "",
        analysis.summary,
        "",
        "## 市场高频技能",
        "",
        _render_list(market_profile.frequent_skills),
        "",
        "## 已覆盖技能",
        "",
        _render_list(analysis.matched_market_skills),
        "",
        "## 缺失技能",
        "",
        _render_list(analysis.missing_market_skills),
        "",
        "## 推荐投递岗位",
        "",
        _render_list(analysis.recommended_roles),
        "",
        "## 简历优化建议",
        "",
        _render_list(analysis.resume_improvement_suggestions),
        "",
        "## 投递策略",
        "",
        _render_list(analysis.delivery_strategy),
        "",
        "## 岗位来源",
        "",
        _render_list(market_profile.source_urls),
    ]

    return "\n".join(lines)


def _render_list(items: list[str]) -> str:
    if not items:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in items)
