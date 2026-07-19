"""Deterministic match scoring."""

from app.schemas.agent_pipeline import EvidenceDecision, JDRequirement, ScoringResult


def _coverage(requirements: list[JDRequirement], decisions: list[EvidenceDecision], category: str) -> float:
    selected = [item for item in requirements if item.category == category]
    if not selected:
        return 0.0
    decision_map = {item.requirement_id: item for item in decisions}
    points = {"supported": 1.0, "partial": 0.45, "missing_evidence": 0.0}
    total_weight = sum(item.weight for item in selected)
    return sum(points[decision_map[item.id].status] * item.weight for item in selected if item.id in decision_map) / max(total_weight, 1)


def score_requirements(
    requirements: list[JDRequirement],
    decisions: list[EvidenceDecision],
    resume_text: str,
) -> ScoringResult:
    must_coverage = _coverage(requirements, decisions, "must")
    preferred_coverage = _coverage(requirements, decisions, "preferred")
    project_relevance = 1.0 if any(
        marker in resume_text for marker in ("项目", "实习", "工作经历", "项目经历")
    ) else 0.0
    if not requirements:
        return ScoringResult(
            score=0,
            must_coverage=0,
            preferred_coverage=0,
            project_relevance=project_relevance,
            review_required=True,
            review_reason="岗位文本未识别出结构化技术要求。",
        )
    score = round(75 * must_coverage + 15 * preferred_coverage + 10 * project_relevance)
    missing_must = any(
        requirement.category == "must"
        and next((item.status for item in decisions if item.requirement_id == requirement.id), "missing_evidence") == "missing_evidence"
        for requirement in requirements
    )
    if missing_must:
        score = min(score, 79)
    return ScoringResult(
        score=score,
        must_coverage=must_coverage,
        preferred_coverage=preferred_coverage,
        project_relevance=project_relevance,
        review_required=False,
    )

