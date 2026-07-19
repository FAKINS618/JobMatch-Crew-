from app.rag.resume_retriever import retrieve_resume_chunks, segment_resume


RESUME_TEXT = """求职目标：Python 后端开发实习

专业技能：
熟悉 Python 和 FastAPI，了解接口设计。

项目经历：
完成任务平台后端开发，负责缓存设计、容器化部署和接口日志排查。
"""


def test_segment_resume_keeps_section_context():
    chunks = segment_resume(RESUME_TEXT)

    assert any(chunk.section == "专业技能" for chunk in chunks)
    assert any(chunk.section == "项目经历" for chunk in chunks)


def test_resume_vector_retriever_returns_relevant_project_chunk():
    chunks = retrieve_resume_chunks(RESUME_TEXT, "Redis 缓存设计", top_k=2)

    assert chunks
    assert chunks[0].section == "项目经历"
    assert "缓存" in chunks[0].content
    assert chunks[0].score > 0
