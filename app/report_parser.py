import json
import re
from typing import Any


def extract_json_block(text: str) -> dict[str, Any]:
    """从大模型原始输出里提取 JSON。

    fallback 解析器：优先匹配 ```json 代码块，找不到时再尝试普通
    花括号 JSON。解析失败返回空 dict，让 service 层继续 raw-only 兜底。
    """
    json_block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)

    if json_block:
        raw_json = json_block.group(1)
    else:
        plain_json = re.search(r"(\{.*\})", text, re.S)
        if not plain_json:
            return {}
        raw_json = plain_json.group(1)

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return {}


def normalize_string_list(value: Any) -> list[str]:
    """把模型输出的列表统一转成字符串列表，兼容旧版 JSON 字段。"""
    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        if isinstance(item, str):
            result.append(item)

        elif isinstance(item, dict):
            parts = []

            day = item.get("day")
            task = item.get("task")
            output = item.get("output")

            if day:
                parts.append(str(day))
            if task:
                parts.append(str(task))
            if output:
                parts.append(f"产出：{output}")

            if parts:
                result.append(" - ".join(parts))
            else:
                result.append(json.dumps(item, ensure_ascii=False))

        else:
            result.append(str(item))

    return result
