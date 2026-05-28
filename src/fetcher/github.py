"""GitHub REST API PR 数据获取器。"""

import re
from urllib.parse import urlparse

import httpx

from src.config.settings import GITHUB_TOKEN
from src.fetcher.base import BaseFetcher
from src.models import PRMetadata, FileChange, ChangeType


GITHUB_API = "https://api.github.com"


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """从 GitHub PR URL 提取 owner / repo / pr_number。

    >>> parse_pr_url("https://github.com/owner/repo/pull/42")
    ('owner', 'repo', 42)
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 4 and path_parts[2] == "pull":
        return path_parts[0], path_parts[1], int(path_parts[3])
    # try to match "github.com/owner/repo/pull/123" even with extra segments
    for i, part in enumerate(path_parts):
        if part == "pull" and i >= 2 and i + 1 < len(path_parts):
            return path_parts[i - 2], path_parts[i - 1], int(path_parts[i + 1])
    raise ValueError(f"无法解析 PR URL: {url}")


class GitHubFetcher(BaseFetcher):
    """通过 GitHub REST API 获取 PR 数据。"""

    def __init__(self, token: str = ""):
        self._token = token or GITHUB_TOKEN
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ai-pr-reviewer",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._client = httpx.Client(
            base_url=GITHUB_API,
            headers=headers,
            timeout=30,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # BaseFetcher 实现
    # ------------------------------------------------------------------

    def fetch_metadata(self, owner: str, repo: str, pr_number: int) -> PRMetadata:
        resp = self._client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        resp.raise_for_status()
        data = resp.json()
        return PRMetadata(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            title=data.get("title", ""),
            body=data.get("body", "") or "",
            author=data.get("user", {}).get("login", ""),
            base_branch=data.get("base", {}).get("ref", ""),
            head_branch=data.get("head", {}).get("ref", ""),
        )

    def fetch_diff(self, owner: str, repo: str, pr_number: int) -> list[FileChange]:
        resp = self._client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100},
        )
        resp.raise_for_status()
        files = resp.json()

        result: list[FileChange] = []
        for f in files:
            status = f.get("status", "modified")
            try:
                change_type = ChangeType(status)
            except ValueError:
                change_type = ChangeType.MODIFIED

            result.append(FileChange(
                filename=f["filename"],
                change_type=change_type,
                diff=f.get("patch", ""),
                additions=f.get("additions", 0),
                deletions=f.get("deletions", 0),
                patch=f.get("patch", ""),
                previous_filename=f.get("previous_filename", ""),
            ))
        return result
