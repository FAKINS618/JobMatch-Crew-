import streamlit as st

from api_client import fetch_role_detail, fetch_roles
from views import (
    render_match_tab,
    render_reports_tab,
    render_role_map_tab,
    render_search_tab,
    render_market_match_tab
)


def main() -> None:
    """Streamlit 前端入口，只负责页面框架和全局状态。"""
    st.set_page_config(
        page_title="CS JobMate",
        page_icon="🎯",
        layout="wide",
    )

    st.title("CS JobMate｜计算机求职简历助手")
    st.caption("基于CrewAI + Fastapi的多 Agent岗位市场画像和结构化评估的简历优化工具")

    try:
        roles = fetch_roles()
    except Exception as exc:
        st.error(f"无法连接后端服务，请先启动 FastAPI。错误：{exc}")
        st.stop()

    if not roles:
        st.error("后端未返回岗位方向，请检查 /api/roles 接口。")
        st.stop()
    st.sidebar.markdown("### 求职目标")
    target_role = st.sidebar.selectbox("目标岗位方向", roles)
    city = st.sidebar.text_input("目标城市", value="北京")
    st.sidebar.success("FastAPI 已连接")


    try:
        role_info = fetch_role_detail(target_role)
    except Exception as exc:
        role_info = {}
        st.sidebar.warning(f"岗位技能图谱读取失败：{exc}")

    match_tab, market_tab, search_tab, reports_tab, role_map_tab = st.tabs(
        ["简历匹配分析", "岗位市场画像", "联网岗位搜索", "历史报告", "岗位技能图谱"]
    )

    with match_tab:
        render_match_tab(target_role=target_role, role_info=role_info)

    with search_tab:
        render_search_tab()

    with reports_tab:
        render_reports_tab()

    with role_map_tab:
        render_role_map_tab(role_info=role_info)

    with market_tab:
        render_market_match_tab(target_role=target_role,default_city=city)


if __name__ == "__main__":
    main()
