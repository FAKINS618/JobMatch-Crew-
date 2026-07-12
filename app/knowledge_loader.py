from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"


def load_knowledge(filename: str) -> str:
    """读取 knowledge/ 下的单个知识文件。"""
    path = KNOWLEDGE_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_interview_knowledge() -> str:
    """读取所有非空 Markdown 知识文件。

    之前这里写死了 4 个文件名；后续补充后端、数据库、RAG、简历优化知识后，
    自动扫描目录更适合扩展，也避免新增知识文件却没有被 Prompt 使用。
    """
    contents = []

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            contents.append(f"# 来源：{path.name}\n\n{text}")

    return "\n\n---\n\n".join(contents)
