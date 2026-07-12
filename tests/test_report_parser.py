from app.report_parser import extract_json_block, normalize_string_list

# 测 JSON 解析器
def test_extract_json_block_from_markdown():
    text = '```json\n{"score": 80, "summary": "分析成功"}\n```'

    data = extract_json_block(text)

    assert data["score"] == 80
    assert data["summary"] == "分析成功"


def test_extract_json_block_from_plain_text():
    text = '模型输出如下：{"score": 75, "summary": "普通 JSON"}'

    data = extract_json_block(text)

    assert data["score"] == 75


def test_extract_json_block_returns_empty_dict_when_invalid():
    text = "这里没有 JSON"

    data = extract_json_block(text)

    assert data == {}


def test_normalize_string_list_handles_dict_items():
    value = [{"day": 1, "task": "学习 FastAPI", "output": "完成接口"}]

    result = normalize_string_list(value)

    assert result == ["1 - 学习 FastAPI - 产出：完成接口"]