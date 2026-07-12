from app.rag.retriever import (
    calc_keyword_score,
    load_knowledge_chunks,
    retrieve_knowledge,
)


def test_load_knowledge_chunks():
    chunks = load_knowledge_chunks()

    assert len(chunks) > 0


def test_calc_keyword_score_matches_fastapi():
    chunks = load_knowledge_chunks()
    fastapi_chunk = next(chunk for chunk in chunks if "FastAPI" in chunk.content)

    score = calc_keyword_score("FastAPI 后端开发", fastapi_chunk)

    assert score > 0


def test_retrieve_knowledge_returns_related_chunks():
    chunks = retrieve_knowledge("Docker 部署 FastAPI 项目", top_k=3)

    assert len(chunks) > 0
    assert any("Docker" in chunk.content or "FastAPI" in chunk.content for chunk in chunks)