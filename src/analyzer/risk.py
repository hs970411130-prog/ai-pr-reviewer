"""风险代码识别 — 检测安全漏洞、空指针、并发问题等。"""

import json

from src.llm.client import chat, _load_prompt
from src.models import FileChange, RiskFinding


_PROMPT = _load_prompt("risk")


def analyze(changes: list[FileChange]) -> list[RiskFinding]:
    """分析一批代码文件，返回风险发现列表。"""
    diff_text = _build_diff_text(changes)
    prompt = _PROMPT.format(diff_text=diff_text)
    response = chat(prompt, system="请严格按 JSON 格式输出。").strip()

    # 提取 JSON 部分（LLM 可能在前后加 markdown 代码块标记）
    response = _extract_json(response)

    try:
        raw = json.loads(response)
    except json.JSONDecodeError:
        return []

    findings: list[RiskFinding] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        findings.append(RiskFinding(
            file=item.get("file", ""),
            line=int(item.get("line", 0) or 0),
            risk_type=item.get("risk_type", ""),
            description=item.get("description", ""),
            suggestion=item.get("suggestion", ""),
            confidence=int(item.get("confidence", 3)),
        ))
    return findings


def _build_diff_text(changes: list[FileChange]) -> str:
    parts: list[str] = []
    for c in changes:
        parts.append(f"### {c.filename}\n```diff\n{c.diff}\n```")
    return "\n\n".join(parts)


def _extract_json(text: str) -> str:
    """去除 LLM 响应中可能的 markdown 代码块包裹。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉第一行 ```json 和最后一行 ```
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines)
    return text
