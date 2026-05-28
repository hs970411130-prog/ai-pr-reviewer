"""PR 变更总结 — 分析全量变更文件，产出 3-5 句中文摘要。"""

from src.llm.client import chat, _load_prompt
from src.models import FileChange, PRMetadata


def summarize(meta: PRMetadata, file_changes: list[FileChange]) -> str:
    """生成 PR 变更摘要。

    使用全量文件列表（含配置/文档），不筛选代码文件。
    """
    prompt_template = _load_prompt("summary")
    file_list = _build_file_list(file_changes)
    prompt = prompt_template
    prompt = prompt.replace("{title}", meta.title)
    prompt = prompt.replace("{body}", meta.body or "(无描述)")
    prompt = prompt.replace("{author}", meta.author)
    prompt = prompt.replace("{base_branch}", meta.base_branch)
    prompt = prompt.replace("{head_branch}", meta.head_branch)
    prompt = prompt.replace("{file_list}", file_list)
    return chat(prompt).strip()


def _build_file_list(changes: list[FileChange]) -> str:
    """构建变更文件的可读列表。"""
    lines: list[str] = []
    for c in changes:
        symbol = {"added": "+", "modified": "M", "removed": "-", "renamed": "R"}.get(
            c.change_type.value, "?"
        )
        filename = c.filename
        if c.previous_filename:
            filename = f"{c.previous_filename} → {c.filename}"
        lines.append(f"  [{symbol}] {filename}  (+{c.additions}/-{c.deletions})")
    return "\n".join(lines)
