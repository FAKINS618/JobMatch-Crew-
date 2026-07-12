from datetime import date, timedelta

from app.schemas import JobPost
from app.services.market_profile_service import (
    build_market_profile,
    calc_freshness_score,
    detect_job_status,
)


def test_detect_expired_job_post():
    post = JobPost(title="Python 实习", content="该职位已关闭")

    status, reason = detect_job_status(post)

    assert status == "expired"
    assert "职位已关闭" in reason


def test_calc_freshness_score_for_recent_post():
    post = JobPost(
        title="Python 实习",
        published_at=date.today() - timedelta(days=3),
    )

    assert calc_freshness_score(post) == 1.0


def test_calc_freshness_score_for_expired_deadline():
    post = JobPost(
        title="Python 实习",
        deadline_at=date.today() - timedelta(days=1),
    )

    assert calc_freshness_score(post) == 0.0


def test_build_market_profile_filters_expired_jobs(monkeypatch):
    def fake_search_jobs(query: str, max_results: int):
        return [
            {
                "title": "Python 后端实习",
                "url": "https://example.com/1",
                "content": "需要 Python FastAPI Docker 项目开发经验",
                "source": "test",
            },
            {
                "title": "已关闭岗位",
                "url": "https://example.com/2",
                "content": "该职位已关闭，需要 Java",
                "source": "test",
            },
        ]

    monkeypatch.setattr(
        "app.services.market_profile_service.search_jobs",
        fake_search_jobs,
    )

    profile, posts = build_market_profile(
        target_role="Python 后端开发",
        city="北京",
        max_results=2,
    )

    assert profile.sample_count == 2
    assert profile.expired_count == 1
    assert profile.unknown_count == 1
    assert "Python" in profile.frequent_skills
    assert "FastAPI" in profile.frequent_skills
    assert len(posts) == 2