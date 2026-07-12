import logging
import json

from app.report_renderer import render_markdown_report
from app.database import save_report
from app.jobmatch_crew import run_jobmatch_crew
from app.report_parser import extract_json_block, normalize_string_list
from app.schemas import JobMatchAnalysis, JobMatchRequest, JobMatchResponse


logger = logging.getLogger(__name__)


def generate_job_match_report(payload: JobMatchRequest) -> JobMatchResponse:
    """运行多 Agent 分析流程，并把生成结果保存到本地数据库。

    这是后端最核心的容错链路：
    1. 理想情况：直接拿到 JobMatchAnalysis，渲染 Markdown 并保存。
    2. 当前兼容方案：从 LLM 原始文本中提取 JSON，再用 Pydantic 本地校验。
    3. 兜底方案：如果结构化校验失败，尽量读取旧版 JSON 字段。
    4. 最低兜底：如果 JSON 都提取失败，保存原始输出，避免接口直接崩溃。

    这样做是为了应对 LLM 输出不稳定、模型接口不支持 response_format 等情况。
    """
    analysis, raw_result = run_jobmatch_crew(
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
        target_role=payload.target_role,
    )

    # 预留主路径：如果未来换成支持 response_format 的模型，
    # run_jobmatch_crew 可以直接返回 JobMatchAnalysis。
    if analysis is not None:
        markdown_report = render_markdown_report(analysis)

        save_report(
            target_role=payload.target_role,
            score=analysis.score,
            resume_text=payload.resume_text,
            jd_text=payload.jd_text,
            markdown_report=markdown_report,
            raw_result=raw_result,
            parsed_result=analysis.model_dump_json(),
            parse_status="pydantic_success",
        )

        return JobMatchResponse(
            score=analysis.score,
            matched_skills=analysis.matched_skills,
            missing_skills=analysis.missing_skills,
            interview_questions=[item.question for item in analysis.interview_questions],
            action_plan=[
                f"第 {item.day} 天：{item.task}；产出：{item.output}"
                for item in analysis.action_plan
            ],
            markdown_report=markdown_report,
            analysis=analysis,
        )

    # 当前主路径：模型输出 JSON 文本，本地负责提取和校验。
    parsed = extract_json_block(raw_result)

    if parsed:
        try:
            analysis = JobMatchAnalysis.model_validate(parsed)
        except Exception as exc:
            logger.warning("Fallback JSON does not match JobMatchAnalysis: %s", exc)
        else:
            markdown_report = render_markdown_report(analysis)
            report_id = save_report(
                target_role=payload.target_role,
                score=analysis.score,
                resume_text=payload.resume_text,
                jd_text=payload.jd_text,
                markdown_report=markdown_report,
                raw_result=raw_result,
                parsed_result=analysis.model_dump_json(),
                parse_status="fallback_pydantic_success",
            )
            logger.info("Saved fallback-pydantic report id=%s", report_id)

            return JobMatchResponse(
                score=analysis.score,
                matched_skills=analysis.matched_skills,
                missing_skills=analysis.missing_skills,
                interview_questions=[
                    item.question for item in analysis.interview_questions
                ],
                action_plan=[
                    f"第 {item.day} 天：{item.task}；产出：{item.output}"
                    for item in analysis.action_plan
                ],
                markdown_report=markdown_report,
                analysis=analysis,
            )

    # raw-only 兜底：没有任何可解析 JSON 时，仍返回原始文本给用户。
    if not parsed:
        report_id = save_report(
            target_role=payload.target_role,
            score=None,
            resume_text=payload.resume_text,
            jd_text=payload.jd_text,
            markdown_report=raw_result,
            raw_result=raw_result,
            parse_status="raw_only",
        )
        logger.info("Saved raw-only report id=%s", report_id)
        return JobMatchResponse(markdown_report=raw_result)

    markdown_report = parsed.get("markdown_report", raw_result)

    # 旧版 fallback：兼容以前模型输出的 score/matched_skills/markdown_report 字段。
    report_id = save_report(
        target_role=payload.target_role,
        score=parsed.get("score"),
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
        markdown_report=markdown_report,
        raw_result=raw_result,
        parsed_result=json.dumps(parsed, ensure_ascii=False),
        parse_status="fallback_json",
    )
    logger.info("Saved fallback-json report id=%s", report_id)

    return JobMatchResponse(
        score=parsed.get("score"),
        matched_skills=normalize_string_list(parsed.get("matched_skills", [])),
        missing_skills=normalize_string_list(parsed.get("missing_skills", [])),
        interview_questions=normalize_string_list(
            parsed.get("interview_questions", [])
        ),
        action_plan=normalize_string_list(parsed.get("action_plan", [])),
        markdown_report=markdown_report,
        analysis=analysis,
    )
