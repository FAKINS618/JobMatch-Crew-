from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = BASE_DIR / "knowledge"


@dataclass
class KnowledgeChunk:
    source: str
    content: str
    score: int = 0


def load_knowledge_chunks() -> list[KnowledgeChunk]:
    """读取 knowledge 目录，并按段落切成知识片段。"""
    chunks = []

    for path in KNOWLEDGE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        parts = [part.strip() for part in text.split("\n\n") if part.strip()]

        for part in parts:
            chunks.append(
                KnowledgeChunk(
                    source=path.name,
                    content=part,
                )
            )

    return chunks


def calc_keyword_score(query: str, chunk: KnowledgeChunk) -> int:
    """用关键词命中次数计算相关性分数。"""
    query_lower = query.lower()
    content_lower = chunk.content.lower()

    score = 0

    keywords = [
        "python",
        "fastapi",
        "django",
        "docker",
        "linux",
        "git",
        "crewai",
        "langchain",
        "rag",
        "向量数据库",
        "prompt",
        "api",
        "mysql",
        "redis",
    ]

    for keyword in keywords:
        if keyword.lower() in query_lower and keyword.lower() in content_lower:
            score += 3

    for word in query_lower.split():
        if len(word) >= 2 and word in content_lower:
            score += 1

    return score


def retrieve_knowledge(query: str, top_k: int = 5) -> list[KnowledgeChunk]:
    """根据查询内容检索最相关的知识片段。"""
    chunks = load_knowledge_chunks()
    scored_chunks = []

    for chunk in chunks:
        score = calc_keyword_score(query, chunk)

        if score > 0:
            chunk.score = score
            scored_chunks.append(chunk)

    scored_chunks.sort(key=lambda item: item.score, reverse=True)

    return scored_chunks[:top_k]


def format_retrieved_knowledge(chunks: list[KnowledgeChunk]) -> str:
    """把检索结果格式化成可注入 Prompt 的文本。"""
    if not chunks:
        return "暂无匹配知识片段。"

    lines = []

    for index, chunk in enumerate(chunks, start=1):
        lines.append(
            f"""### 知识片段 {index}
来源：{chunk.source}
相关性分数：{chunk.score}

{chunk.content}
"""
        )

    return "\n\n".join(lines)