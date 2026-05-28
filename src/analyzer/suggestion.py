"""Review 建议生成 — 代码可读性、性能、最佳实践等方面的建议。"""

import json

from src.llm.client import chat, _load_prompt
from src.models import FileChange, SuggestionFinding


_PROMPT = _load_prompt("suggestion")


def analyze(changes: list[FileChange]) -> list[SuggestionFinding]:
    """分析一批代码文件，返回建议列表。"""
    diff_text = _build_diff_text(changes)
    prompt = _PROMPT.format(diff_text=diff_text)
    response = chat(prompt, system="请严格按 JSON 格式输出。").strip()
    response = _extract_json(response)

    try:
        raw = json.loads(response)
    except json.JSONDecodeError:
        return []

    findings: list[SuggestionFinding] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        findings.append(SuggestionFinding(
            file=item.get("file", ""),
            line=int(item.get("line", 0) or 0),
            category=item.get("category", ""),
            description=item.get("description", ""),
            confidence=int(item.get("confidence", 3)),
        ))
    return findings


def _build_diff_text(changes: list[FileChange]) -> str:
    parts: list[str] = []
    for c in changes:
        parts.append(f"### {c.filename}\n```diff\n{c.diff}\n```")
    return "\n\n".join(parts)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines)
    return text
