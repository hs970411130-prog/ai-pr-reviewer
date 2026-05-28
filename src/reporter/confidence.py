"""置信度评分与去重 — 对分析结果后处理。"""

from src.models import RiskFinding, SuggestionFinding


def deduplicate_risks(risks: list[RiskFinding]) -> list[RiskFinding]:
    """去除重复的风险发现（同文件同行号同类型的合并）。"""
    seen: set[tuple[str, int, str]] = set()
    result: list[RiskFinding] = []
    for r in risks:
        key = (r.file, r.line, r.risk_type)
        if key not in seen:
            seen.add(key)
            result.append(r)
    return result


def deduplicate_suggestions(
    suggestions: list[SuggestionFinding]
) -> list[SuggestionFinding]:
    """去除重复的建议。"""
    seen: set[tuple[str, int, str]] = set()
    result: list[SuggestionFinding] = []
    for s in suggestions:
        key = (s.file, s.line, s.category)
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def confidence_label(score: int) -> str:
    """将 1-5 的置信度分值转为可读标签。"""
    labels = {
        5: "🔴 确定",
        4: "🟠 很可能",
        3: "🟡 可能",
        2: "🟢 不太可能",
        1: "⚪ 几乎不可能",
    }
    return labels.get(score, f"未知({score})")
