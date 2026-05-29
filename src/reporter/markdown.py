"""Markdown report generator."""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label


def _is_test_file(filename: str) -> bool:
    parts = filename.lower().replace("\\", "/").split("/")
    return any(p.startswith("test") or p.endswith("_test") for p in parts)


def generate(report: AnalysisReport) -> str:
    meta = report.pr_metadata
    lines: list[str] = []

    # Title
    lines.append(f"# PR Review Report")
    lines.append("")
    lines.append(f"**PR:** [{meta.title}](https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number})")
    lines.append(f"**Repo:** {meta.owner}/{meta.repo}  ")
    lines.append(f"**Author:** {meta.author}  ")
    lines.append(f"**Branch:** {meta.base_branch} <- {meta.head_branch}")
    lines.append("")

    # PR description
    if meta.body:
        lines.append("## PR Description")
        lines.append("")
        # Indent to avoid conflict with report structure headers
        for bline in meta.body.split("\n"):
            lines.append(f"> {bline}" if bline.strip() else ">")
        lines.append("")

    # File change list (FIX 3)
    if report.file_changes:
        lines.append("## Changed Files")
        lines.append("")
        lines.append("| File | Changes |")
        lines.append("|------|---------|")
        for fc in report.file_changes:
            symbol = {"added": "+", "modified": "M", "removed": "-", "renamed": "R"}.get(fc.change_type.value, "?")
            lines.append(f"| [{symbol}] {fc.filename} | +{fc.additions}/-{fc.deletions} |")
        lines.append("")

    # Summary
    if report.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(report.summary)
        lines.append("")

    # Context (FIX 4: only show if meaningful)
    if report.context and report.context.analysis_text :
        lines.append("## Context")
        lines.append("")
        lines.append(report.context.analysis_text)
        lines.append("")

    # Risks - split into source and test (FIX 5)
    source_risks = [r for r in report.risks if not _is_test_file(r.file)]
    test_risks = [r for r in report.risks if _is_test_file(r.file)]

    if source_risks:
        lines.append("## Risk Findings")
        lines.append("")
        lines.append("| File | Line | Type | Description | Suggestion | Confidence |")
        lines.append("|------|------|------|-------------|------------|------------|")
        for r in source_risks:
            lines.append(
                f"| {r.file} | {r.line} | {r.risk_type} | {r.description} "
                f"| {r.suggestion} | {confidence_label(r.confidence)} |"
            )
        lines.append("")

    if test_risks:
        lines.append("## Test Code Risks")
        lines.append("")
        lines.append("| File | Line | Type | Description | Suggestion | Confidence |")
        lines.append("|------|------|------|-------------|------------|------------|")
        for r in test_risks:
            lines.append(
                f"| {r.file} | {r.line} | {r.risk_type} | {r.description} "
                f"| {r.suggestion} | {confidence_label(r.confidence)} |"
            )
        lines.append("")

    # Suggestions - split source and test
    source_sug = [s for s in report.suggestions if not _is_test_file(s.file)]
    test_sug = [s for s in report.suggestions if _is_test_file(s.file)]

    if source_sug:
        lines.append("## Review Suggestions")
        lines.append("")
        lines.append("| File | Line | Category | Description | Confidence |")
        lines.append("|------|------|----------|-------------|------------|")
        for s in source_sug:
            lines.append(
                f"| {s.file} | {s.line} | {s.category} "
                f"| {s.description} | {confidence_label(s.confidence)} |"
            )
        lines.append("")

    if test_sug:
        lines.append("## Test Code Suggestions")
        lines.append("")
        lines.append("| File | Line | Category | Description | Confidence |")
        lines.append("|------|------|----------|-------------|------------|")
        for s in test_sug:
            lines.append(
                f"| {s.file} | {s.line} | {s.category} "
                f"| {s.description} | {confidence_label(s.confidence)} |"
            )
        lines.append("")

    # Skipped files
    if report.skipped_files:
        lines.append("## Skipped Files (too large)")
        lines.append("")
        for f in report.skipped_files:
            lines.append(f"- {f}")
        lines.append("")

    return "\n".join(lines)
