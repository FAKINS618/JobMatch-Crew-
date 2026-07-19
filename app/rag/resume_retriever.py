"""简历分段与轻量向量检索。

当前版本使用标准库实现 TF-IDF，避免首次启用时下载 embedding 模型。
检索结果只负责召回候选证据，最终匹配结论仍由 CrewAI 和规则校验共同决定。
"""

from collections import Counter
from dataclasses import dataclass, replace
import math
import re


SECTION_PATTERN = re.compile(
    r"^(?:\d+[.、)]?\s*)?(技能|技能概览|专业技能|项目经历|项目经验|实习经历|工作经历|教育背景|教育经历|证书|奖项|自我评价|求职目标|实践经历)\s*[:：]?\s*$",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#./-]*|[\u4e00-\u9fff]+")

REQUIREMENT_QUERY_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "FastAPI": ("异步接口", "后端接口", "web api"),
    "RESTful API": ("接口设计", "服务端接口", "api 接口"),
    "MySQL": ("关系型数据库", "sql 数据库"),
    "Redis": ("缓存", "分布式缓存"),
    "Docker": ("容器化", "容器部署"),
    "RAG": ("检索增强", "知识库问答"),
    "大模型 API": ("大语言模型", "llm", "openai", "deepseek"),
    "Prompt": ("提示词", "提示工程"),
}


@dataclass(frozen=True)
class ResumeChunk:
    chunk_id: str
    section: str
    content: str
    score: float = 0.0


def requirement_query(requirement: str) -> str:
    """为岗位要求构造检索查询，扩展词只用于召回，不直接判定匹配。"""
    return " ".join((requirement, *REQUIREMENT_QUERY_EXPANSIONS.get(requirement, ())))


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.finditer(text.lower()):
        value = match.group(0)
        if re.fullmatch(r"[\u4e00-\u9fff]+", value):
            tokens.append(value)
            tokens.extend(value[index : index + 2] for index in range(len(value) - 1))
        else:
            tokens.append(value)
    return tokens


def _split_long_chunk(section: str, content: str, max_chars: int = 420) -> list[str]:
    normalized = " ".join(content.split())
    if len(normalized) <= max_chars:
        return [normalized]
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(0, end - 60)
    return chunks


def segment_resume(text: str) -> list[ResumeChunk]:
    """按常见简历区块切分文本，缺少标题时按长度切分。"""
    chunks: list[ResumeChunk] = []
    section = "简历正文"
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        content = "\n".join(buffer).strip()
        if content:
            for index, part in enumerate(_split_long_chunk(section, content)):
                chunks.append(
                    ResumeChunk(
                        chunk_id=f"resume-{len(chunks) + 1}",
                        section=section,
                        content=part,
                    )
                )
        buffer = []

    for line in text.splitlines():
        stripped = line.strip()
        header = SECTION_PATTERN.match(stripped)
        if header:
            flush()
            section = header.group(1)
            continue
        if stripped:
            buffer.append(stripped)
        elif buffer:
            flush()
    flush()

    if chunks:
        return chunks
    return [
        ResumeChunk(chunk_id=f"resume-{index + 1}", section="简历正文", content=part)
        for index, part in enumerate(_split_long_chunk("简历正文", text))
        if part
    ]


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left).intersection(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def retrieve_resume_chunks(
    resume_text: str, query: str, top_k: int = 3, min_score: float = 0.05
) -> list[ResumeChunk]:
    """使用 TF-IDF 向量召回与岗位要求相关的简历片段。"""
    chunks = segment_resume(resume_text)
    documents = [_tokens(chunk.content) for chunk in chunks]
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    document_frequency = Counter(
        token for tokens in documents for token in set(tokens)
    )
    total_documents = len(documents)

    def vectorize(tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        return {
            token: (1 + math.log(count))
            * (math.log((total_documents + 1) / (document_frequency[token] + 1)) + 1)
            for token, count in counts.items()
        }

    query_vector = vectorize(query_tokens)
    scored = [
        replace(chunk, score=_cosine_similarity(query_vector, vectorize(tokens)))
        for chunk, tokens in zip(chunks, documents)
    ]
    return [chunk for chunk in sorted(scored, key=lambda item: item.score, reverse=True) if chunk.score >= min_score][:top_k]


def format_resume_evidence(chunks: list[ResumeChunk]) -> str:
    if not chunks:
        return "暂无可召回的简历证据。"
    return "\n".join(
        f"- [{chunk.section}] 向量相似度 {chunk.score:.2f}：{chunk.content}"
        for chunk in chunks
    )
