"""LLM 批量分析通用工具 — risk.py 和 suggestion.py 的共享逻辑。"""

import json
import re

from src.llm.client import chat, _load_prompt
from src.models import FileChange


def build_diff_text(changes: list[FileChange]) -> str:
    """将一批 FileChange 拼接为 LLM 可读的 diff 文本。"""
    parts: list[str] = []
    for c in changes:
        parts.append(f"### {c.filename}\n```diff\n{c.diff}\n```")
    return "\n\n".join(parts)


def extract_json(text: str) -> str:
    """从 LLM 响应中提取 JSON 部分，处理 markdown 代码块等噪音。"""
    text = text.strip()
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)
        text = text.strip()
    if text.startswith("{") and not text.startswith("[{"):
        text = "[" + text + "]"
    return text


def parse_json_response(response: str) -> list[dict]:
    """解析 LLM 返回的 JSON 数组，容错处理。"""
    raw = None
    try:
        raw = json.loads(response)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", response, re.DOTALL)
        if m:
            try:
                raw = json.loads(m.group())
            except json.JSONDecodeError:
                pass

    if raw is None:
        return []
    if not isinstance(raw, list):
        raw = [raw]
    return [item for item in raw if isinstance(item, dict)]


def run_llm_batch(
    changes: list[FileChange],
    prompt_name: str,
    system: str = "请严格按 JSON 格式输出。",
) -> list[dict]:
    """通用 LLM 批量分析：拼 diff → 调 LLM → 解析 JSON。"""
    diff_text = build_diff_text(changes)
    prompt = _load_prompt(prompt_name).replace("{diff_text}", diff_text)
    response = chat(prompt, system=system).strip()
    response = extract_json(response)
    return parse_json_response(response)
