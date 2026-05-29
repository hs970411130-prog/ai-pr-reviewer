"""Single-file HTML report generator - zero external dependencies."""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label


def _is_test_file(filename: str) -> bool:
    parts = filename.lower().replace("\\", "/").split("/")
    return any(p.startswith("test") or p.endswith("_test") for p in parts)


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _risk_table(risks, title):
    if not risks:
        return ""
    html = f"<h2>{_esc(title)}</h2><table><tr><th>File</th><th>Line</th><th>Type</th><th>Description</th><th>Suggestion</th><th>Confidence</th></tr>"
    for r in risks:
        html += f"<tr><td>{_esc(r.file)}</td><td>{r.line}</td><td>{_esc(r.risk_type)}</td><td>{_esc(r.description)}</td><td>{_esc(r.suggestion)}</td><td>{confidence_label(r.confidence)}</td></tr>"
    html += "</table>"
    return html


def _sug_table(suggestions, title):
    if not suggestions:
        return ""
    html = f"<h2>{_esc(title)}</h2><table><tr><th>File</th><th>Line</th><th>Category</th><th>Description</th><th>Confidence</th></tr>"
    for s in suggestions:
        html += f"<tr><td>{_esc(s.file)}</td><td>{s.line}</td><td>{_esc(s.category)}</td><td>{_esc(s.description)}</td><td>{confidence_label(s.confidence)}</td></tr>"
    html += "</table>"
    return html


def generate(report: AnalysisReport) -> str:
    meta = report.pr_metadata
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PR Review - {_esc(meta.title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.6; }}
  h1 {{ border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
  h2 {{ margin-top: 32px; color: #1e40af; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; font-size: 14px; }}
  th {{ background: #f3f4f6; }}
  .meta {{ color: #6b7280; font-size: 14px; }}
  .skipped {{ color: #9ca3af; font-size: 13px; }}
  .pr-body {{ background: #f9fafb; padding: 12px 16px; border-left: 3px solid #2563eb; white-space: pre-wrap; font-size: 14px; }}
</style>
</head>
<body>
<h1>PR Review Report</h1>
<p class="meta">
  <strong>PR:</strong> <a href="https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number}">{_esc(meta.title)}</a><br>
  <strong>Repo:</strong> {meta.owner}/{meta.repo} | 
  <strong>Author:</strong> {meta.author} | 
  <strong>Branch:</strong> {meta.base_branch} <- {meta.head_branch}
</p>
"""

    # PR description
    if meta.body:
        html += f"<h2>PR Description</h2><div class='pr-body'>{_esc(meta.body)}</div>"

    # File changes
    if report.file_changes:
        html += "<h2>Changed Files</h2><table><tr><th>File</th><th>Changes</th></tr>"
        for fc in report.file_changes:
            symbol = {"added": "+", "modified": "M", "removed": "-", "renamed": "R"}.get(fc.change_type.value, "?")
            html += f"<tr><td>[{symbol}] {_esc(fc.filename)}</td><td>+{fc.additions}/-{fc.deletions}</td></tr>"
        html += "</table>"

    # Summary
    if report.summary:
        html += f"<h2>Summary</h2><p>{_esc(report.summary)}</p>"

    # Context
    if report.context and report.context.analysis_text :
        html += f"<h2>Context</h2><p>{_esc(report.context.analysis_text)}</p>"

    # Risks - split
    source_risks = [r for r in report.risks if not _is_test_file(r.file)]
    test_risks = [r for r in report.risks if _is_test_file(r.file)]
    html += _risk_table(source_risks, "Risk Findings")
    html += _risk_table(test_risks, "Test Code Risks")

    # Suggestions - split
    source_sug = [s for s in report.suggestions if not _is_test_file(s.file)]
    test_sug = [s for s in report.suggestions if _is_test_file(s.file)]
    html += _sug_table(source_sug, "Review Suggestions")
    html += _sug_table(test_sug, "Test Code Suggestions")

    # Skipped
    if report.skipped_files:
        html += "<h2>Skipped Files (too large)</h2><ul class='skipped'>"
        for f in report.skipped_files:
            html += f"<li>{_esc(f)}</li>"
        html += "</ul>"

    html += "</body></html>"
    return html
