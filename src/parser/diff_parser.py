"""Diff 解析器 — 将 unified diff 结构化，提取变更细节。

Parser 不参与文件过滤（那是 Engine 的事），只做纯数据转换。
"""

import re

from src.models import FileChange

# Unified diff header line patterns
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", re.MULTILINE)
_ADDED_LINE_RE = re.compile(r"^\+(?!\+\+)")
_REMOVED_LINE_RE = re.compile(r"^-(?!--)")


def extract_added_lines(diff: str) -> list[str]:
    """从 diff 中提取新增的代码行（去掉 + 前缀）。"""
    lines: list[str] = []
    for line in diff.split("\n"):
        if _ADDED_LINE_RE.match(line):
            lines.append(line[1:])
    return lines


def extract_removed_lines(diff: str) -> list[str]:
    """从 diff 中提取删除的代码行（去掉 - 前缀）。"""
    lines: list[str] = []
    for line in diff.split("\n"):
        if _REMOVED_LINE_RE.match(line):
            lines.append(line[1:])
    return lines


def is_empty_diff(change: FileChange) -> bool:
    """判断 FileChange 是否没有实际 diff 内容。"""
    return not change.diff.strip()


def count_diff_hunks(change: FileChange) -> int:
    """统计一个文件的 diff 包含几个 hunk（变更块）。"""
    return len(_HUNK_HEADER_RE.findall(change.diff))
