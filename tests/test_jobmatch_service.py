from app.services.jobmatch_service import build_degraded_markdown_report


def test_degraded_report_hides_raw_model_output():
    report = build_degraded_markdown_report()

    assert "原始内容" in report
    assert "{" not in report


def test_degraded_report_keeps_recognized_fields_only():
    report = build_degraded_markdown_report(
        {
            "score": 82,
            "summary": "候选人的后端开发经历与岗位要求较为匹配。",
            "matched_skills": ["Python", "FastAPI"],
        }
    )

    assert "参考评分：82/100" in report
    assert "Python" in report
    assert "FastAPI" in report
