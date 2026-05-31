"""Review 建议生成 — 代码可读性、性能、最佳实践等方面的建议。"""

from src.analyzer._batch import run_llm_batch
from src.models import FileChange, SuggestionFinding


def analyze(changes: list[FileChange]) -> list[SuggestionFinding]:
    """分析一批代码文件，返回建议列表。"""
    items = run_llm_batch(changes, "suggestion")
    findings: list[SuggestionFinding] = []
    for item in items:
        findings.append(SuggestionFinding(
            file=item.get("file", ""),
            line=int(item.get("line", 0) or 0),
            category=item.get("category", ""),
            description=item.get("description", ""),
            confidence=int(item.get("confidence", 3)),
        ))
    return findings
