"""分析调度引擎 — 文件过滤、分批、并行调度 LLM 调用。

这是分块策略的唯一执行点：Parser 给全量，Engine 决定谁看什么。
"""

import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config.settings import SKIP_EXTENSIONS, MAX_FILES_PER_BATCH, MAX_CHARS_PER_FILE
from src.models import FileChange

logger = logging.getLogger(__name__)
_MAX_CONCURRENT_BATCHES = 5


def filter_code_files(changes: list[FileChange]) -> list[FileChange]:
    """过滤掉非代码文件，返回仅代码文件的列表。"""
    result: list[FileChange] = []
    for c in changes:
        ext = "." + c.filename.rsplit(".", 1)[-1].lower() if "." in c.filename else ""
        if ext not in SKIP_EXTENSIONS:
            result.append(c)
    return result


def chunk_files(changes: list[FileChange]) -> list[list[FileChange]]:
    """将文件列表按分批规则切分为多批。

    规则：
    - 每批 1~3 个文件
    - 单文件超过 MAX_CHARS_PER_FILE 跳过
    """
    batches: list[list[FileChange]] = []
    current_batch: list[FileChange] = []

    for change in changes:
        if len(change.diff) > MAX_CHARS_PER_FILE:
            continue
        current_batch.append(change)
        if len(current_batch) >= MAX_FILES_PER_BATCH:
            batches.append(current_batch)
            current_batch = []

    if current_batch:
        batches.append(current_batch)

    return batches


def find_skipped_files(changes: list[FileChange]) -> list[str]:
    """返回因过大被跳过的文件名列表。"""
    return [c.filename for c in changes if len(c.diff) > MAX_CHARS_PER_FILE]


def run_analysis(
    changes: list[FileChange],
    analyze_fn,
    filter_code: bool = True,
) -> list:
    """通用分析执行器：过滤 → 分批 → 并行调 LLM → 聚合结果。

    Args:
        changes: 全量 FileChange 列表
        analyze_fn: 单批分析函数，签名为 fn(batch: list[FileChange]) -> list
        filter_code: 是否先过滤代码文件

    Returns:
        所有批次结果的合并列表
    """
    files = filter_code_files(changes) if filter_code else list(changes)
    batches = chunk_files(files)

    if not batches:
        return []

    results: list = []
    max_workers = min(len(batches), _MAX_CONCURRENT_BATCHES)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_fn, batch): batch for batch in batches}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                batch = futures[future]
                filenames = [f.filename for f in batch]
                logger.warning("Analysis failed for %s: %s", filenames, e)
                logger.debug(traceback.format_exc())

    return results
