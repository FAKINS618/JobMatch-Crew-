from app.schemas import JobMarketProfile, JobPost, MarketDataQuality, MarketMatchRequest
from app.services import market_match_service


def test_insufficient_market_data_skips_llm_and_returns_trend_only(monkeypatch):
    profile = JobMarketProfile(
        target_role="AI 应用开发实习",
        sample_count=8,
        valid_count=0,
        unknown_count=8,
        frequent_skills=["Python"],
        data_quality=MarketDataQuality(
            level="low",
            active_job_count=0,
            source_domain_count=0,
            message="有效岗位样本不足，仅展示技能趋势，不生成投递结论。",
        ),
    )
    posts = [JobPost(title="AI 应用开发实习", status="unknown")]
    saved_report = {}

    monkeypatch.setattr(
        market_match_service,
        "build_market_profile",
        lambda **_kwargs: (profile, posts),
    )
    monkeypatch.setattr(
        market_match_service,
        "build_llm",
        lambda: (_ for _ in ()).throw(AssertionError("不应调用 LLM")),
    )
    monkeypatch.setattr(
        market_match_service,
        "save_report",
        lambda **kwargs: saved_report.update(kwargs) or 1,
    )
    monkeypatch.setattr(market_match_service, "save_job_posts", lambda **_kwargs: None)

    result = market_match_service.generate_market_match_report(
        MarketMatchRequest(
            resume_text="Python FastAPI CrewAI RAG 项目经历与后端开发实践。" * 4,
            target_role="AI 应用开发实习",
        )
    )

    assert result.analysis.score is None
    assert result.analysis.job_recommendations == []
    assert "0 条可确认仍在招聘" in result.analysis.summary
    assert saved_report["parse_status"] == "skipped_insufficient_market_data"
    assert saved_report["raw_result"] is None


def test_relevant_trend_data_returns_trend_score_without_delivery_score(monkeypatch):
    profile = JobMarketProfile(
        target_role="AI 应用开发实习",
        sample_count=8,
        relevant_count=4,
        valid_count=0,
        unknown_count=4,
        frequent_skills=["Python", "FastAPI", "RAG"],
        data_quality=MarketDataQuality(level="low"),
    )
    monkeypatch.setattr(
        market_match_service,
        "build_market_profile",
        lambda **_kwargs: (profile, []),
    )
    monkeypatch.setattr(market_match_service, "save_report", lambda **_kwargs: 1)
    monkeypatch.setattr(market_match_service, "save_job_posts", lambda **_kwargs: None)

    result = market_match_service.generate_market_match_report(
        MarketMatchRequest(
            resume_text="Python 和 FastAPI 项目经验。" * 10,
            target_role="AI 应用开发实习",
        )
    )

    assert result.analysis.trend_score == 67
    assert result.analysis.delivery_score is None
    assert result.analysis.matched_market_skills == ["FastAPI", "Python"]
    assert result.analysis.missing_market_skills == ["RAG"]
