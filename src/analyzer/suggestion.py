"""Review 建议生成 — 代码可读性、性能、最佳实践等方面的建议。"""

import json
import re

from src.llm.client import chat, _load_prompt
from src.models import FileChange, SuggestionFinding


_PROMPT = _load_prompt("suggestion")


def analyze(changes: list[FileChange]) -> list[SuggestionFinding]:
    """分析一批代码文件，返回建议列表。"""
    diff_text = _build_diff_text(changes)
    prompt = _PROMPT.replace("{diff_text}", diff_text)
    response = chat(prompt, system="请严格按 JSON 格式输出。").strip()
    response = _extract_json(response)


    raw = None
    try:
        raw = json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON array from response
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
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    # If still has markdown fence inside, try again
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text)
        text = text.strip()
    # Wrap single object in array
    if text.startswith("{") and not text.startswith("[{"):
        text = "[" + text + "]"
    return text