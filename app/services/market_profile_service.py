from collections import Counter
from datetime import date

from app.schemas import JobMarketProfile, JobPost
from app.search_service import search_jobs


# 岗位画像服务：
# 负责把联网搜索到的原始岗位结果，清洗成可用于简历匹配分析的市场画像。

SKILL_KEYWORDS = [
    "Python",
    "FastAPI",
    "Flask",
    "Django",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Linux",
    "Git",
    "RESTful API",
    "大模型 API",
    "Prompt",
    "CrewAI",
    "LangChain",
    "RAG",
    "向量数据库",
    "Vue",
    "React",
    "TypeScript",
]


TOOL_KEYWORDS = [
    "Docker",
    "Git",
    "Linux",
    "Apifox",
    "Postman",
    "MySQL",
    "Redis",
    "Chroma",
    "Milvus",
]

EXPIRED_KEYWORDS = [
    "已下线",
    "停止招聘",
    "职位已关闭",
    "岗位已关闭",
    "招满",
    "已结束",
    "过期",
    "页面不存在",
    "404",
]


def build_market_profile(
    target_role: str,
    city: str = "",
    max_results: int = 8,
) -> tuple[JobMarketProfile, list[JobPost]]:
    """搜索真实岗位，并从岗位内容中提取高频技能和要求。

    返回二元组：
    - JobMarketProfile：给前端和 LLM 使用的聚合画像；
    - list[JobPost]：保留原始岗位样本，后续写入 job_posts 表用于追溯。
    """
    query = f"{target_role} 实习 招聘 {city} 最近发布".strip()
    raw_results = search_jobs(query=query, max_results=max_results)
    posts = []
    for item in raw_results:
        text = f"{item.get('title') or ''}\n{item.get('content') or ''}"
        published_at, deadline_at = extract_job_dates(text)
        post = JobPost(
            title=item.get("title") or "",
            url=item.get("url") or "",
            content=item.get("content") or "",
            source=item.get("source") or "",
            published_at=published_at,
            deadline_at=deadline_at,
        )

        post.status, post.invalid_reason = detect_job_status(post)
        post.freshness_score = calc_freshness_score(post)

        posts.append(post)

    # 过期岗位不参与画像统计；发布时间未知的岗位保留，但用较低权重参与统计。
    usable_posts = [post for post in posts if is_usable_post(post)]

    skill_counter = Counter()
    tool_counter = Counter()
    responsibilities = []
    project_requirements = []
    source_urls = []

    for post in usable_posts:
        text = f"{post.title}\n{post.content}"
        lower_text = text.lower()

        for skill in SKILL_KEYWORDS:
            if skill.lower() in lower_text:
                # 按 freshness_score 加权，避免旧岗位和新岗位拥有同等影响力。
                skill_counter[skill] += post.freshness_score

        for tool in TOOL_KEYWORDS:
            if tool.lower() in lower_text:
                tool_counter[tool] += post.freshness_score

        if post.content:
            responsibilities.append(post.content[:160])

        if any(word in text for word in ["项目", "经验", "开发", "系统"]):
            project_requirements.append(post.content[:160])

        if post.url:
            source_urls.append(post.url)

    market_profile = JobMarketProfile(
        target_role=target_role,
        sample_count=len(posts),
        valid_count=len([post for post in posts if post.status == "active"]),
        expired_count=len([post for post in posts if post.status == "expired"]),
        unknown_count=len([post for post in posts if post.status == "unknown"]),
        freshness_level=calc_freshness_level(usable_posts),
        frequent_skills=[item for item, _ in skill_counter.most_common(10)],
        frequent_tools=[item for item, _ in tool_counter.most_common(8)],
        project_requirements=project_requirements[:5],
        common_responsibilities=responsibilities[:5],
        source_urls=source_urls[:10],
    )

    return market_profile, posts


def detect_job_status(post: JobPost) -> tuple[str, str]:
    """判断岗位是否疑似过期。"""
    text = f"{post.title}\n{post.content}"

    for keyword in EXPIRED_KEYWORDS:
        if keyword in text:
            return "expired", f"命中过期关键词：{keyword}"

    if post.deadline_at and post.deadline_at < date.today():
        return "expired", "投递截止日期已过"

    if post.published_at:
        return "active", ""

    return "unknown", "未提取到发布时间"


def calc_freshness_score(post: JobPost) -> float:
    """根据发布时间和截止时间计算岗位时效分。"""
    today = date.today()

    if post.deadline_at and post.deadline_at < today:
        return 0.0

    if post.published_at is None:
        return 0.5

    days = (today - post.published_at).days

    if days <= 7:
        return 1.0
    if days <= 30:
        return 0.8
    if days <= 90:
        return 0.4

    return 0.0


def calc_freshness_level(posts: list[JobPost]) -> str:
    """把多个岗位的平均时效分转换成前端可展示的等级。"""
    if not posts:
        return "low"

    avg_score = sum(post.freshness_score for post in posts) / len(posts)

    if avg_score >= 0.8:
        return "high"
    if avg_score >= 0.5:
        return "medium"

    return "low"


def is_usable_post(post: JobPost) -> bool:
    """判断岗位是否参与市场画像统计。"""
    if post.status == "expired":
        return False

    if post.freshness_score <= 0:
        return False

    return True

def extract_job_dates(text: str) -> tuple[date | None, date | None]:
    """从岗位文本中提取发布时间和截止时间。

    先返回 None，后续再用正则识别：
    - 发布于 2026-07-10
    - 3 天前
    - 截止时间 2026-08-01

    这个函数的价值是把“岗位是否新鲜”的判断从 Prompt 中拿出来，
    交给后端规则处理，避免 LLM 主观判断过期信息。
    """
    return None, None
