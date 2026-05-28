"""Fetcher 抽象接口。"""

from abc import ABC, abstractmethod

from src.models import PRMetadata, FileChange


class BaseFetcher(ABC):
    """PR 数据获取器抽象基类。"""

    @abstractmethod
    def fetch_metadata(self, owner: str, repo: str, pr_number: int) -> PRMetadata:
        """获取 PR 基本信息。"""
        ...

    @abstractmethod
    def fetch_diff(self, owner: str, repo: str, pr_number: int) -> list[FileChange]:
        """获取 PR 变更文件列表及 diff。"""
        ...
