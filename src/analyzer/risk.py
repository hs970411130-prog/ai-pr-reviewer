"""风险代码识别 — 检测安全漏洞、空指针、并发问题等。"""

from src.analyzer._batch import run_llm_batch
from src.models import FileChange, RiskFinding


def analyze(changes: list[FileChange]) -> list[RiskFinding]:
    """分析一批代码文件，返回风险发现列表。"""
    items = run_llm_batch(changes, "risk")
    findings: list[RiskFinding] = []
    for item in items:
        findings.append(RiskFinding(
            file=item.get("file", ""),
            line=int(item.get("line", 0) or 0),
            risk_type=item.get("risk_type", ""),
            description=item.get("description", ""),
            suggestion=item.get("suggestion", ""),
            confidence=int(item.get("confidence", 3)),
        ))
    return findings
