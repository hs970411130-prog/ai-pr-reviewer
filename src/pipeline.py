"""全链路编排 — 从 PR URL 到最终报告的完整流程。"""

import os

from src.fetcher.github import GitHubFetcher, parse_pr_url
from src.analyzer.engine import run_analysis, filter_code_files, find_skipped_files
from src.analyzer import summary, risk, suggestion, context
from src.reporter import confidence, markdown, web
from src.models import AnalysisReport


def run(pr_url: str, github_token: str = "") -> AnalysisReport:
    """执行完整分析流程。

    1. 解析 URL → 拉取数据
    2. Summary（全量文件）
    3. Risk + Suggestion（内部并行：ThreadPoolExecutor）
    4. Context
    5. 聚合 + 去重 + 置信度
    """
    owner, repo, pr_num = parse_pr_url(pr_url)
    fetcher = GitHubFetcher(token=github_token)

    meta = fetcher.fetch_metadata(owner, repo, pr_num)
    changes = fetcher.fetch_diff(owner, repo, pr_num)

    summary_text = summary.summarize(meta, changes)

    code_only = filter_code_files(changes)
    risks_raw = run_analysis(code_only, risk.analyze, filter_code=False)
    suggestions_raw = run_analysis(code_only, suggestion.analyze, filter_code=False)

    ctx = context.enhance(meta, changes)

    report = AnalysisReport(
        pr_metadata=meta,
        summary=summary_text,
        risks=confidence.deduplicate_risks(risks_raw),
        suggestions=confidence.deduplicate_suggestions(suggestions_raw),
        context=ctx,
        file_changes=changes,
        skipped_files=find_skipped_files(changes),
    )
    return report


def run_and_save(
    pr_url: str, github_token: str = "", output_dir: str = "."
) -> tuple[AnalysisReport, str, str]:
    """执行分析并保存 Markdown + HTML 报告。

    Returns:
        (report, md_path, html_path)
    """
    report = run(pr_url, github_token)

    md = markdown.generate(report)
    html_content = web.generate(report)

    dir_name = (
        f"{report.pr_metadata.owner}-{report.pr_metadata.repo}"
        f"-{report.pr_metadata.pr_number}"
    )
    report_dir = os.path.join(os.path.abspath(output_dir), dir_name)
    os.makedirs(report_dir, exist_ok=True)
    md_path = os.path.join(report_dir, "report.md")
    html_path = os.path.join(report_dir, "report.html")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return report, md_path, html_path
