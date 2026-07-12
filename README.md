# JobMatch Crew

基于 CrewAI + FastAPI + Streamlit 的计算机专业求职简历分析助手。

## 项目简介

JobMatch Crew 是一个面向计算机专业学生和 AI 应用开发实习求职者的多 Agent 系统。用户输入简历和岗位 JD 后，系统会由多个 Agent 协作生成求职匹配报告，包括岗位要求分析、简历能力分析、匹配评分、技能缺口、简历优化建议、面试题和 7 天补强计划。

## 技术栈

- Python
- FastAPI
- Pydantic
- CrewAI
- DeepSeek / OpenAI-compatible API
- Streamlit
- SQLite
- Tavily Search
- Uvicorn
- uv

## 核心功能

- JD 分析
- 简历能力分析
- 岗位匹配评分
- 简历优化建议
- 面试题生成
- 7 天补强计划
- Markdown 报告下载
- 历史报告保存
- 岗位技能图谱
- 联网岗位搜索

## 项目结构

```text
jobmatch-crew/
├── app/
│   ├── api/                 # FastAPI 路由层
│   ├── services/            # 业务编排层
│   ├── prompts/             # Agent Prompt 模板
│   ├── main.py              # FastAPI 应用入口
│   ├── jobmatch_crew.py     # CrewAI 多 Agent 核心流程
│   ├── database.py          # SQLite 报告存储
│   └── role_skill_map.py    # 岗位技能图谱
├── schemas/
│   ├── api.py              # 接口请求/响应模型
│   ├── analysis.py         # LLM 结构化分析模型
│   └── __init__.py
├── frontend/
│   ├── streamlit_app.py     # Streamlit 前端入口
│   ├── views.py             # 前端页面模块
│   ├── ui_helpers.py        # 前端展示辅助函数
│   └── api_client.py        # 后端接口客户端
├── examples/                # 示例简历、JD、输出报告
├── knowledge/               # 面试知识库
└── main.py                  # 后端快捷启动脚本
```

## 本地运行

安装依赖：

```bash
uv sync
```

启动 FastAPI 后端：

```bash
uv run uvicorn app.main:app --reload
```

或使用快捷入口：

```bash
uv run python main.py
```

启动 Streamlit 前端：

```bash
uv run streamlit run frontend/streamlit_app.py
```

访问接口文档：

```text
http://127.0.0.1:8000/docs
```

## 二期新增能力：岗位市场画像

用户无需手动复制 JD，只需要上传简历并选择目标方向，系统会自动联网搜索真实实习岗位，提取高频技能和项目要求，生成岗位市场画像，并评估用户简历与当前市场需求的匹配度。