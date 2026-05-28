"""单文件 HTML 报告生成器 — 零外部依赖。"""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label


def generate(report: AnalysisReport) -> str:
    """将分析报告渲染为独立 HTML 页面。"""
    meta = report.pr_metadata
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PR Review — {_escape(meta.title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.6; }}
  h1 {{ border-bottom: 2px solid #2563eb; padding-bottom: 8px; }}
  h2 {{ margin-top: 32px; color: #1e40af; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; font-size: 14px; }}
  th {{ background: #f3f4f6; }}
  .meta {{ color: #6b7280; font-size: 14px; }}
  .skipped {{ color: #9ca3af; font-size: 13px; }}
  .risk-high {{ background: #fef2f2; }}
</style>
</head>
<body>
<h1>PR Review 报告</h1>
<p class="meta">
  <strong>PR:</strong> <a href="https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number}">{_escape(meta.title)}</a><br>
  <strong>仓库:</strong> {meta.owner}/{meta.repo} &nbsp;|&nbsp;
  <strong>作者:</strong> {meta.author} &nbsp;|&nbsp;
  <strong>分支:</strong> {meta.base_branch} ← {meta.head_branch}
</p>
"""

    if report.summary:
        html += f"<h2>变更摘要</h2><p>{_escape(report.summary)}</p>"

    if report.context and report.context.related_issues:
        html += "<h2>上下文分析</h2><ul>"
        for issue in report.context.related_issues:
            html += f"<li>{_escape(issue)}</li>"
        html += "</ul>"

    if report.risks:
        html += "<h2>风险发现</h2><table><tr><th>文件</th><th>行号</th><th>类型</th><th>描述</th><th>建议</th><th>置信度</th></tr>"
        for r in report.risks:
            html += f"<tr><td>{_escape(r.file)}</td><td>{r.line}</td><td>{_escape(r.risk_type)}</td><td>{_escape(r.description)}</td><td>{_escape(r.suggestion)}</td><td>{confidence_label(r.confidence)}</td></tr>"
        html += "</table>"

    if report.suggestions:
        html += "<h2>Review 建议</h2><table><tr><th>文件</th><th>行号</th><th>类别</th><th>描述</th><th>置信度</th></tr>"
        for s in report.suggestions:
            html += f"<tr><td>{_escape(s.file)}</td><td>{s.line}</td><td>{_escape(s.category)}</td><td>{_escape(s.description)}</td><td>{confidence_label(s.confidence)}</td></tr>"
        html += "</table>"

    if report.skipped_files:
        html += "<h2>跳过的文件（过大）</h2><ul class='skipped'>"
        for f in report.skipped_files:
            html += f"<li>{_escape(f)}</li>"
        html += "</ul>"

    html += "</body></html>"
    return html


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
