"""Markdown report generator."""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label


def _is_test_file(filename: str) -> bool:
    parts = filename.lower().replace("\\", "/").split("/")
    return any(p.startswith("test") or p.endswith("_test") for p in parts)


def _esc_md(text: str) -> str:
    """转义 Markdown 表格中的特殊字符。"""
    return str(text).replace("|", "\\|").replace("\n", " ")


def generate(report: AnalysisReport) -> str:
    meta = report.pr_metadata
    lines: list[str] = []

    lines.append("# PR Review Report")
    lines.append("")
    lines.append(
        f"**PR:** [{meta.title}]"
        f"(https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number})"
    )
    lines.append(f"**Repo:** {meta.owner}/{meta.repo}  ")
    lines.append(f"**Author:** {meta.author}  ")
    lines.append(f"**Branch:** {meta.base_branch} <- {meta.head_branch}")
    lines.append("")

    if meta.body:
        lines.append("## PR Description")
        lines.append("")
        for bline in meta.body.split("\n"):
            lines.append(f"> {bline}" if bline.strip() else ">")
        lines.append("")

    if report.file_changes:
        lines.append("## Changed Files")
        lines.append("")
        lines.append("| File | Changes |")
        lines.append("|------|---------|")
        for fc in report.file_changes:
            symbol = {"added": "+", "modified": "M", "removed": "-", "renamed": "R"}.get(
                fc.change_type.value, "?"
            )
            lines.append(f"| [{symbol}] {_esc_md(fc.filename)} | +{fc.additions}/-{fc.deletions} |")
        lines.append("")

    if report.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(report.summary)
        lines.append("")

    if report.context and report.context.analysis_text:
        lines.append("## Context")
        lines.append("")
        lines.append(report.context.analysis_text)
        lines.append("")

    source_risks = [r for r in report.risks if not _is_test_file(r.file)]
    test_risks = [r for r in report.risks if _is_test_file(r.file)]

    if source_risks:
        lines.append("## Risk Findings")
        lines.append("")
        lines.append("| File | Line | Type | Description | Suggestion | Confidence |")
        lines.append("|------|------|------|-------------|------------|------------|")
        for r in source_risks:
            lines.append(
                f"| {_esc_md(r.file)} | {r.line} | {_esc_md(r.risk_type)} "
                f"| {_esc_md(r.description)} | {_esc_md(r.suggestion)} "
                f"| {confidence_label(r.confidence)} |"
            )
        lines.append("")

    if test_risks:
        lines.append("## Test Code Risks")
        lines.append("")
        lines.append("| File | Line | Type | Description | Suggestion | Confidence |")
        lines.append("|------|------|------|-------------|------------|------------|")
        for r in test_risks:
            lines.append(
                f"| {_esc_md(r.file)} | {r.line} | {_esc_md(r.risk_type)} "
                f"| {_esc_md(r.description)} | {_esc_md(r.suggestion)} "
                f"| {confidence_label(r.confidence)} |"
            )
        lines.append("")

    source_sug = [s for s in report.suggestions if not _is_test_file(s.file)]
    test_sug = [s for s in report.suggestions if _is_test_file(s.file)]

    if source_sug:
        lines.append("## Review Suggestions")
        lines.append("")
        lines.append("| File | Line | Category | Description | Confidence |")
        lines.append("|------|------|----------|-------------|------------|")
        for s in source_sug:
            lines.append(
                f"| {_esc_md(s.file)} | {s.line} | {_esc_md(s.category)} "
                f"| {_esc_md(s.description)} | {confidence_label(s.confidence)} |"
            )
        lines.append("")

    if test_sug:
        lines.append("## Test Code Suggestions")
        lines.append("")
        lines.append("| File | Line | Category | Description | Confidence |")
        lines.append("|------|------|----------|-------------|------------|")
        for s in test_sug:
            lines.append(
                f"| {_esc_md(s.file)} | {s.line} | {_esc_md(s.category)} "
                f"| {_esc_md(s.description)} | {confidence_label(s.confidence)} |"
            )
        lines.append("")

    if report.skipped_files:
        lines.append("## Skipped Files (too large)")
        lines.append("")
        for f in report.skipped_files:
            lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines)
