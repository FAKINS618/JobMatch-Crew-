"""Report construction from validated structures only."""

import json

from app.agent_pipeline.structured_runner import StageOutcome, run_structured
from app.config import settings
from app.schemas import ActionPlanItem, InterviewQuestion, JobMatchAnalysis, RequirementMatch, ScoreDimension
from app.schemas.agent_pipeline import (
    EvidenceCandidate,
    EvidenceDecision,
    JDRequirement,
    ReportNarrative,
    ScoringResult,
)


REPORT_PROMPT_VERSION = "v1"


def _deterministic_report(
    requirements: list[JDRequirement],
    candidates: dict[str, list[EvidenceCandidate]],
    decisions: list[EvidenceDecision],
    score: ScoringResult,
) -> JobMatchAnalysis:
    candidate_map = {item.id: item for values in candidates.values() for item in values}
    decision_map = {item.requirement_id: item for item in decisions}
    matched: list[str] = []
    missing: list[str] = []
    dimensions: list[ScoreDimension] = []
    matches: list[RequirementMatch] = []
    for requirement in requirements:
        decision = decision_map.get(requirement.id)
        if decision is None:
            continue
        evidence = [candidate_map[item].snippet for item in decision.evidence_ids if item in candidate_map]
        if decision.status == "supported":
            matched.append(requirement.skill)
        else:
            missing.append(requirement.skill)
        matches.append(
            RequirementMatch(
                requirement=requirement.skill,
                category=requirement.category,
                status=decision.status,
                keyword_evidence=evidence if decision.status == "supported" else [],
                semantic_evidence=evidence if decision.status == "partial" else [],
                confidence=decision.confidence,
                suggestion="保留并量化该能力的项目证据。" if decision.status == "supported" else "补充与该能力相关的真实项目产出。",
            )
        )
        dimensions.append(
            ScoreDimension(
                name=requirement.skill,
                score=10 if decision.status == "supported" else 5 if decision.status == "partial" else 0,
                max_score=10,
                evidence=evidence,
                suggestion=matches[-1].suggestion,
            )
        )
    return JobMatchAnalysis(
        score=score.score,
        summary=f"基于 {len(requirements)} 项岗位要求，简历直接覆盖 {len(matched)} 项，确定性证据匹配分为 {score.score}/100。",
        matched_skills=matched,
        missing_skills=missing,
        score_dimensions=dimensions,
        requirement_matches=matches,
        action_plan=[
            ActionPlanItem(day=index + 1, task=f"补强 {skill} 的项目或练习证据", output=f"一段可核验的 {skill} 项目说明或链接")
            for index, skill in enumerate(missing[:3])
        ],
        interview_questions=[
            InterviewQuestion(question=f"请结合项目说明 {skill} 的实现与取舍。", skill=skill, reason="该岗位要求尚缺少充分简历证据。")
            for skill in missing[:3]
        ],
        risk_points=[score.review_reason] if score.review_required and score.review_reason else [],
    )


def write_report(
    requirements: list[JDRequirement],
    candidates: dict[str, list[EvidenceCandidate]],
    decisions: list[EvidenceDecision],
    score: ScoringResult,
    *,
    use_llm: bool,
) -> tuple[JobMatchAnalysis, bool, StageOutcome]:
    deterministic = _deterministic_report(requirements, candidates, decisions, score)
    structured_input = {
        "requirements": [item.model_dump() for item in requirements],
        "decisions": [item.model_dump() for item in decisions],
        "score": score.model_dump(),
    }
    prompt = f"""
    你是报告表达 Agent。只能使用下面的结构化岗位要求、证据裁决和确定性评分。
    不得看到或推断完整简历和 JD，不得把建议写成已验证事实。
    输出必须符合 ReportNarrative JSON schema，只生成摘要、风险、面试题和行动建议。

    {json.dumps(structured_input, ensure_ascii=False)}
    """
    try:
        outcome = run_structured(
            prompt=prompt,
            output_model=ReportNarrative,
            expected_output="符合 ReportNarrative 的 JSON 对象",
            enabled=use_llm,
            cache_namespace="analysis:report_narrative",
            cache_identity={
                "structured_input": structured_input,
                "model": settings.model,
                "prompt_version": REPORT_PROMPT_VERSION,
                "schema_version": "ReportNarrative-v1",
            },
            cache_ttl_seconds=24 * 60 * 60,
        )
        if outcome.value is None:
            return deterministic, True, outcome
        narrative = outcome.value
        merged = deterministic.model_copy(
            update={
                "summary": narrative.summary,
                "resume_bullets": narrative.resume_bullets,
                "interview_questions": narrative.interview_questions,
                "action_plan": narrative.action_plan,
                "risk_points": narrative.risk_points,
            }
        )
        return merged, outcome.degraded, outcome
    except Exception as error:
        # Keep the deterministic facts even if a caller supplies a broken mock.
        fallback = StageOutcome(
            value=None,
            validation_error=f"report merge: {type(error).__name__}: {str(error)[:400]}",
            degraded=True,
        )
        return deterministic, True, fallback
