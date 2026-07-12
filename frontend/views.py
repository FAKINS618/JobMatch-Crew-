from typing import Any
import streamlit as st
from api_client import (
    create_job_match_report,
    get_report_detail,
    list_reports,
    search_jobs,
    create_market_match_task,
    get_task_detail,
)
from ui_helpers import format_tags, get_role_core_skills, split_matched_skills


def render_score_overview(data: dict[str, Any]) -> None:
    """展示简历匹配报告的核心指标。"""
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    metric_col1.metric("匹配评分", data.get("score") or "未解析")
    metric_col2.metric("已匹配技能", len(data.get("matched_skills", [])))
    metric_col3.metric("缺失技能", len(data.get("missing_skills", [])))
    metric_col4.metric("面试题数量", len(data.get("interview_questions", [])))


def render_structured_analysis(analysis: dict[str, Any]) -> None:
    """展示后端返回的结构化分析结果。"""
    if not analysis:
        return

    st.markdown("### 结构化分析")

    score_dimensions = analysis.get("score_dimensions", [])
    if score_dimensions:
        st.markdown("#### 分项评分")

        for item in score_dimensions:
            name = item.get("name", "未命名维度")
            score = item.get("score", 0)
            max_score = item.get("max_score", 1)

            st.markdown(f"**{name}：{score}/{max_score}**")
            st.progress(min(score / max_score, 1.0))

            evidence = item.get("evidence", [])
            if evidence:
                st.caption("评分依据")
                for text in evidence:
                    st.markdown(f"- {text}")

            suggestion = item.get("suggestion")
            if suggestion:
                st.info(suggestion)

    bullets = analysis.get("resume_bullets", [])
    if bullets:
        st.markdown("#### 简历 Bullet 建议")
        for bullet in bullets:
            st.markdown(f"- {bullet}")

    questions = analysis.get("interview_questions", [])
    if questions:
        st.markdown("#### 面试问题")
        for q in questions:
            st.markdown(f"- **{q.get('question', '')}**")
            st.caption(f"考察技能：{q.get('skill', '')}；原因：{q.get('reason', '')}")

    action_plan = analysis.get("action_plan", [])
    if action_plan:
        st.markdown("#### 补强计划")
        for item in action_plan:
            st.markdown(
                f"- 第 {item.get('day')} 天：{item.get('task')}；产出：{item.get('output', '')}"
            )

def render_market_quality(profile: dict[str, Any]) -> None:
    """展示岗位市场画像的数据质量。"""
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("搜索岗位", profile.get("sample_count", 0))
    col2.metric("有效岗位", profile.get("valid_count", 0))
    col3.metric("疑似过期", profile.get("expired_count", 0))
    col4.metric("时效可信度", profile.get("freshness_level", "unknown"))

    fetched_at = profile.get("fetched_at")
    if fetched_at:
        st.caption(f"数据抓取时间：{fetched_at}")

def render_market_match_result(data: dict[str, Any]) -> None:
    """展示岗位市场匹配分析结果。"""
    profile = data.get("market_profile", {})
    analysis = data.get("analysis", {})

    render_market_quality(profile)

    st.markdown("### 市场匹配结论")
    st.metric("市场匹配分", analysis.get("score", "未解析"))

    summary = analysis.get("summary")
    if summary:
        st.write(summary)

    st.markdown("### 市场高频技能")
    st.markdown(format_tags(profile.get("frequent_skills", [])))

    st.markdown("### 缺失技能")
    st.markdown(format_tags(analysis.get("missing_market_skills", [])))

    st.markdown("### 推荐投递岗位")
    for item in analysis.get("recommended_roles", []):
        st.markdown(f"- {item}")

    st.markdown("### 简历优化建议")
    for item in analysis.get("resume_improvement_suggestions", []):
        st.markdown(f"- {item}")

    st.markdown("### 投递策略")
    for item in analysis.get("delivery_strategy", []):
        st.markdown(f"- {item}")

    st.markdown("### 完整报告")
    st.markdown(data.get("markdown_report", ""))

def render_match_tab(target_role: str, role_info: dict[str, Any]) -> None:
    """简历和岗位 JD 匹配分析页。

    页面职责：收集输入、做本地关键词快速检查、调用后端生成报告、
    展示结构化分析和完整 Markdown 报告。
    """
    st.subheader("简历匹配分析")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "上传简历文件（支持 txt / md）",
            type=["txt", "md"],
        )

        uploaded_resume_text = ""
        if uploaded_file is not None:
            uploaded_resume_text = uploaded_file.read().decode("utf-8")
            st.success("简历文件解析成功")

        resume_text = st.text_area(
            "简历内容",
            value=uploaded_resume_text,
            height=360,
            placeholder="请粘贴你的简历内容，或上传 txt/md 文件...",
        )

        if resume_text.strip() and role_info:
            core_skills = get_role_core_skills(role_info)
            matched_skills, missing_skills = split_matched_skills(
                resume_text,
                core_skills,
            )

            st.caption("这里是关键词快速检查，最终结果以多 Agent 分析报告为准。")
            match_col, miss_col = st.columns(2)

            with match_col:
                st.markdown("#### 已出现技能")
                st.markdown(format_tags(matched_skills))

            with miss_col:
                st.markdown("#### 未出现技能")
                st.markdown(format_tags(missing_skills))

    with col2:
        jd_text = st.text_area(
            "岗位 JD",
            height=360,
            placeholder="请粘贴岗位 JD...",
        )

    if st.button("生成求职分析报告", type="primary", use_container_width=True):
        if len(resume_text.strip()) < 80 or len(jd_text.strip()) < 80:
            st.warning("请提供更完整的简历和岗位 JD，建议每项不少于 80 字。")
            return

        try:
            with st.spinner("多 Agent 正在分析，请稍等..."):
                data = create_job_match_report(
                    {
                        "resume_text": resume_text,
                        "jd_text": jd_text,
                        "target_role": target_role,
                    }
                )
        except Exception as exc:
            st.error(f"生成失败：{exc}")
            return

        render_score_overview(data)
        analysis = data.get("analysis")
        render_structured_analysis(analysis)

        st.markdown("### 完整报告")
        markdown_report = data.get("markdown_report", "")
        st.markdown(markdown_report)
        st.download_button(
            label="下载 Markdown 报告",
            data=markdown_report,
            file_name="jobmatch_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


def render_search_tab() -> None:
    """联网岗位搜索页。"""
    st.subheader("联网岗位搜索")

    search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
    with search_col1:
        keyword = st.text_input("岗位关键词", value="Python AI 应用开发")
    with search_col2:
        city = st.text_input("城市", value="北京")
    with search_col3:
        max_results = st.slider("搜索结果数量", 1, 10, 5)

    if st.button("搜索岗位", type="primary"):
        try:
            with st.spinner("正在联网搜索岗位..."):
                results = search_jobs(
                    {
                        "keyword": keyword,
                        "city": city,
                        "max_results": max_results,
                    }
                ).get("results", [])
        except Exception as exc:
            st.error(f"搜索失败：{exc}")
            return

        if not results:
            st.info("暂未搜索到岗位结果，请换一个关键词试试。")
            return

        for index, item in enumerate(results, start=1):
            st.markdown(f"### {index}. {item.get('title') or '未命名岗位'}")
            st.markdown(item.get("content") or "")
            if item.get("url"):
                st.markdown(f"[查看原链接]({item.get('url')})")
            st.divider()


def render_reports_tab() -> None:
    """历史报告列表和详情页。"""
    st.subheader("历史报告")

    try:
        reports = list_reports().get("reports", [])
    except Exception as exc:
        st.error(f"读取历史报告失败：{exc}")
        return

    if not reports:
        st.info("暂无历史报告。生成一次简历分析后，这里会出现记录。")
        return

    selected_report = st.selectbox(
        "选择历史报告",
        reports,
        format_func=lambda item: (
            f"#{item.get('id')} | {item.get('target_role')} | "
            f"分数：{item.get('score')} | {item.get('created_at')}"
        ),
    )

    if st.button("查看报告详情", type="primary"):
        try:
            detail = get_report_detail(int(selected_report["id"]))
        except Exception as exc:
            st.error(f"读取报告详情失败：{exc}")
            return

        st.markdown(detail.get("markdown_report", ""))

        job_posts = detail.get("job_posts", [])
        if job_posts:
            st.markdown("### 本次参考岗位")

            for post in job_posts:
                title = post.get("title") or "未命名岗位"

                with st.expander(title):
                    st.caption(
                        f"状态：{post.get('status', 'unknown')} | "
                        f"时效分：{post.get('freshness_score', 0)} | "
                        f"来源：{post.get('source', '')}"
                    )

                    content = post.get("content") or ""
                    if content:
                        st.write(content[:500])

                    url = post.get("url")
                    if url:
                        st.markdown(f"[查看岗位来源]({url})")


def render_role_map_tab(role_info: dict[str, Any]) -> None:
    """岗位技能图谱页。"""
    st.subheader("岗位技能图谱")

    if not role_info:
        st.info("暂无岗位技能图谱。")
        return

    skill_col, project_col, priority_col = st.columns(3)

    with skill_col:
        st.markdown("#### 核心技能")
        st.markdown(format_tags(get_role_core_skills(role_info)))

    with project_col:
        st.markdown("#### 推荐项目关键词")
        for keyword in role_info.get("project_keywords", []):
            st.markdown(f"- {keyword}")

    with priority_col:
        st.markdown("#### 学习优先级")
        for index, item in enumerate(role_info.get("learning_priority", []), start=1):
            st.markdown(f"{index}. {item}")


def render_market_match_tab(target_role: str, default_city: str = "北京") -> None:
    """基于目标方向自动搜索岗位，并分析简历与市场需求的匹配度。"""
    if "market_task_id" not in st.session_state:
        st.session_state.market_task_id = None
    if "market_task_detail" not in st.session_state:
        st.session_state.market_task_detail = None

    st.subheader("岗位市场画像")

    resume_text = st.text_area(
        "简历内容",
        height=360,
        placeholder="请粘贴你的简历内容...",
        key="market_resume_text",
    )

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("城市", value=default_city, key="market_match_city")
    with col2:
        max_results = st.slider("岗位样本数量", 3, 15, 8)

    if st.button("生成岗位市场匹配分析", type="primary", use_container_width=True):
        if len(resume_text.strip()) < 80:
            st.warning("请提供更完整的简历内容。")
            return

        try:
            with st.spinner("正在搜索岗位并分析市场需求..."):
                task = create_market_match_task(
                    {
                        "resume_text": resume_text,
                        "target_role": target_role,
                        "city": city,
                        "max_results": max_results,
                    }
                )

        except Exception as exc:
            st.error(f"分析失败：{exc}")
            return

        st.session_state.market_task_id = task["task_id"]
        st.session_state.market_task_detail = task
        st.success(f"任务已提交，任务 ID：{task['task_id']}")

    # Streamlit 点击任意按钮都会整页重跑。
    # 因此任务状态区必须放在“生成任务”按钮外面，否则点击刷新时不会进入生成按钮分支。
    if st.session_state.market_task_id:
        st.markdown("### 任务状态")
        st.caption(f"当前任务 ID：{st.session_state.market_task_id}")

        if st.button("刷新任务状态", use_container_width=True):
            try:
                task = get_task_detail(st.session_state.market_task_id)
            except Exception as exc:
                st.error(f"任务状态查询失败：{exc}")
                return

            st.session_state.market_task_detail = task

        task = st.session_state.market_task_detail or {}
        progress = int(task.get("progress") or 0)
        status = task.get("status") or "pending"

        st.progress(progress)
        st.write(f"当前状态：{status}")

        if status == "failed":
            st.error(task.get("error_message") or "任务执行失败")

        if status == "success" and task.get("report_id"):
            try:
                detail = get_report_detail(int(task["report_id"]))
            except Exception as exc:
                st.error(f"读取分析报告失败：{exc}")
                return

            st.success("分析完成")
            st.markdown(detail.get("markdown_report", ""))


