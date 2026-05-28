"""数据模型定义 — 项目中所有结构化数据的 dataclass。

所有模块间的数据传递都使用这里定义的类型，避免散落各处的 dict。
"""

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# PR 相关
# ---------------------------------------------------------------------------

@dataclass
class PRMetadata:
    """GitHub PR 的基本信息。"""
    owner: str
    repo: str
    pr_number: int
    title: str
    body: str = ""
    author: str = ""
    base_branch: str = ""
    head_branch: str = ""


# ---------------------------------------------------------------------------
# 文件变更
# ---------------------------------------------------------------------------

class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """单个文件的变更信息。

    diff 字段存储 unified diff 原文，供 LLM 分析使用。
    """
    filename: str
    change_type: ChangeType
    diff: str                      # unified diff 原文
    additions: int = 0
    deletions: int = 0
    patch: str = ""                # 同 diff，GitHub API 标准字段
    previous_filename: str = ""    # rename 时的旧文件名


# ---------------------------------------------------------------------------
# 分析结果
# ---------------------------------------------------------------------------

@dataclass
class RiskFinding:
    """单条风险发现。"""
    file: str
    line: int                     # 0 表示文件级别
    risk_type: str                # 安全漏洞 / 空指针 / 并发问题 / 资源泄漏 等
    description: str
    suggestion: str = ""
    confidence: int = 3           # 1-5，越高越确定


@dataclass
class SuggestionFinding:
    """单条 Review 建议。"""
    file: str
    line: int
    category: str                 # 代码风格 / 性能 / 可读性 / 最佳实践 等
    description: str
    confidence: int = 3


@dataclass
class ContextInfo:
    """上下文增强信息。"""
    related_issues: list[str] = field(default_factory=list)
    file_blame_info: dict[str, str] = field(default_factory=dict)  # filename -> blame summary
    document_changes: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """一次完整分析的报告，聚合所有子模块结果。"""
    pr_metadata: PRMetadata
    summary: str = ""
    risks: list[RiskFinding] = field(default_factory=list)
    suggestions: list[SuggestionFinding] = field(default_factory=list)
    context: ContextInfo | None = None
    file_changes: list[FileChange] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)  # 因过大跳过的文件
