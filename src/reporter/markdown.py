"""Markdown 报告生成器。"""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label


def generate(report: AnalysisReport) -> str:
    """将分析报告渲染为 Markdown 字符串。"""
    meta = report.pr_metadata
    lines: list[str] = []

    # 标题
    lines.append(f"# PR Review 报告")
    lines.append(f"")
    lines.append(f"**PR:** [{meta.title}](https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number})")
    lines.append(f"**仓库:** {meta.owner}/{meta.repo}  ")
    lines.append(f"**作者:** {meta.author}  ")
    lines.append(f"**分支:** {meta.base_branch} ← {meta.head_branch}")
    lines.append("")

    # 摘要
    if report.summary:
        lines.append("## 变更摘要")
        lines.append("")
        lines.append(report.summary)
        lines.append("")

    # 上下文
    if report.context and report.context.analysis_text:
        lines.append("## 上下文分析")
        lines.append("")
        lines.append(report.context.analysis_text)
        lines.append("")

    # 风险
    if report.risks:
        lines.append("## 风险发现")
        lines.append("")
        lines.append("| 文件 | 行号 | 类型 | 描述 | 建议 | 置信度 |")
        lines.append("|------|------|------|------|------|--------|")
        for r in report.risks:
            lines.append(
                f"| {r.file} | {r.line} | {r.risk_type} | {r.description} "
                f"| {r.suggestion} | {confidence_label(r.confidence)} |"
            )
        lines.append("")

    # 建议
    if report.suggestions:
        lines.append("## Review 建议")
        lines.append("")
        lines.append("| 文件 | 行号 | 类别 | 描述 | 置信度 |")
        lines.append("|------|------|------|------|--------|")
        for s in report.suggestions:
            lines.append(
                f"| {s.file} | {s.line} | {s.category} "
                f"| {s.description} | {confidence_label(s.confidence)} |"
            )
        lines.append("")

    # 跳过文件
    if report.skipped_files:
        lines.append("## 跳过的文件（过大）")
        lines.append("")
        for f in report.skipped_files:
            lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines)
