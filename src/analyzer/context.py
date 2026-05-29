"""上下文增强 — 内部拆分：拉取 GitHub 数据 + LLM 上下文分析。"""

import httpx
from src.config.settings import GITHUB_TOKEN
from src.llm.client import chat, _load_prompt
import re
from src.models import PRMetadata, FileChange, ContextInfo

GITHUB_API = "https://api.github.com"
_PROMPT = _load_prompt("context")


def enhance(meta: PRMetadata, file_changes: list[FileChange]) -> ContextInfo:
    """获取 PR 上下文信息并生成增强分析。

    内部两段：
    1. _fetch_context_data() — 拉取 GitHub 数据
    2. _analyze_context()     — LLM 分析
    """
    data = _fetch_context_data(meta, file_changes)
    analysis = _analyze_context(meta, data)
    data.analysis_text = analysis
    return data


# ------------------------------------------------------------------
# 第一阶段：拉取数据
# ------------------------------------------------------------------

def _fetch_context_data(meta: PRMetadata, changes: list[FileChange]) -> ContextInfo:
    """从 GitHub API 拉取 Issue 引用、文档变更等。"""
    info = ContextInfo()

    # 文档变更
    info.document_changes = [
        c.filename for c in changes
        if c.filename.endswith((".md", ".rst", ".txt", ".adoc"))
    ]

    # 关联 Issue（从 PR body 中提取 #xxx 引用）
    info.related_issues = _extract_issue_refs(meta.body)

    # git blame 信息（仅对非新增文件）
    info.file_blame_info = _fetch_blame_summaries(meta, changes)

    return info


def _extract_issue_refs(body: str) -> list[str]:
    """从 PR body 中提取 #123 格式的 Issue 引用。"""
    import re
    return re.findall(r"#(\d+)", body)


def _fetch_blame_summaries(
    meta: PRMetadata, changes: list[FileChange]
) -> dict[str, str]:
    """获取变更文件的主要维护者信息。"""
    if not GITHUB_TOKEN:
        return {}

    client = httpx.Client(
        base_url=GITHUB_API,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-pr-reviewer",
        },
        timeout=15,
            follow_redirects=True,
    )

    result: dict[str, str] = {}
    for c in changes:
        if c.change_type.value == "added":
            continue  # 新文件没有 blame 信息
        try:
            resp = client.get(
                f"/repos/{meta.owner}/{meta.repo}/commits",
                params={"path": c.filename, "per_page": 1},
            )
            if resp.status_code == 200 and resp.json():
                commit = resp.json()[0]
                author = commit.get("commit", {}).get("author", {}).get("name", "")
                date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
                result[c.filename] = f"最后修改: {author} ({date})"
            else:
                result[c.filename] = "(无历史)"
        except Exception:
            result[c.filename] = "(获取失败)"

    return result


# ------------------------------------------------------------------
# 第二阶段：LLM 分析
# ------------------------------------------------------------------

def _analyze_context(meta: PRMetadata, info: ContextInfo) -> str:
    """用 LLM 生成上下文分析文本。"""
    issues = ", ".join(f"#{i}" for i in info.related_issues) or "(无)"
    doc = "\n".join(info.document_changes) or "(无文档变更)"
    blame = "\n".join(f"  {k}: {v}" for k, v in info.file_blame_info.items()) or "(无)"

    prompt = _PROMPT
    prompt = prompt.replace("{title}", meta.title)
    prompt = prompt.replace("{body}", meta.body or "(无)")
    prompt = prompt.replace("{issues}", issues)
    prompt = prompt.replace("{doc_changes}", doc)
    prompt = prompt.replace("{blame_info}", blame)
    result = chat(prompt).strip()
    # Strip leading markdown headers the LLM might generate
    result = re.sub(r"^#{1,4}\s*[^\n]*\n+", "", result).strip()
    return result
