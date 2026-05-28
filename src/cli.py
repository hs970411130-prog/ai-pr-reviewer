"""CLI 入口。"""

import os
import sys

import click

from src.pipeline import run_and_save


@click.command()
@click.argument("pr_url")
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token（也可通过 GITHUB_TOKEN 环境变量设置）",
)
@click.option(
    "--output-dir", "-o",
    default=".",
    help="报告输出目录（默认当前目录）",
)
def main(pr_url: str, github_token: str, output_dir: str):
    """AI PR Review 助手 — 自动分析 GitHub Pull Request。

    PR_URL: GitHub PR 地址，如 https://github.com/owner/repo/pull/42
    """
    if not github_token:
        click.echo("错误: 未设置 GitHub Token。请通过 --github-token 或环境变量 GITHUB_TOKEN 提供。", err=True)
        sys.exit(1)

    if "DEEPSEEK_API_KEY" not in os.environ:
        click.echo("警告: 未设置 DEEPSEEK_API_KEY 环境变量，LLM 调用将失败。", err=True)

    click.echo(f"正在分析: {pr_url}")
    click.echo(f"输出目录: {os.path.abspath(output_dir)}")
    click.echo("")

    try:
        report = run_and_save(pr_url, github_token=github_token, output_dir=output_dir)
    except Exception as e:
        click.echo(f"分析失败: {e}", err=True)
        sys.exit(1)

    md_file = f"pr-review-{report.pr_metadata.owner}-{report.pr_metadata.repo}-{report.pr_metadata.pr_number}.md"
    click.echo(f"✅ 报告已生成:")
    click.echo(f"   Markdown: {os.path.join(os.path.abspath(output_dir), md_file)}")
    click.echo(f"   HTML:     {os.path.join(os.path.abspath(output_dir), md_file.replace('.md', '.html'))}")

    # 简要输出
    click.echo(f"\n📋 摘要: {report.summary}")
    click.echo(f"⚠️  风险发现: {len(report.risks)} 条")
    click.echo(f"💡 Review 建议: {len(report.suggestions)} 条")
    if report.skipped_files:
        click.echo(f"⏭️  跳过文件: {len(report.skipped_files)} 个")


if __name__ == "__main__":
    main()
