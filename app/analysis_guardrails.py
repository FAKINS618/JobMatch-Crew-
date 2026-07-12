from app.schemas import JobMatchAnalysis


def validate_jobmatch_analysis(output):
    data = output.pydantic or output.json_dict

    if data is None:
        return False, "没有生成结构化分析结果"

    if isinstance(data, dict):
        try:
            data = JobMatchAnalysis.model_validate(data)
        except Exception as exc:
            return False, f"结构化结果校验失败：{exc}"

    if len(data.score_dimensions) < 4:
        return False, "分项评分至少需要 4 个维度"

    if len(data.interview_questions) < 5:
        return False, "面试题至少需要 5 个"

    if len(data.action_plan) < 7:
        return False, "补强计划至少需要 7 天"

    if data.score < 90 and not data.missing_skills:
        return False, "低于 90 分时必须说明缺失技能"

    return True, data