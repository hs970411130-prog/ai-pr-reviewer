# PR Review Report

**PR:** [fix: guard FDCapture.snap() against prematurely closed tmpfile](https://github.com/pytest-dev/pytest/pull/14531)
**Repo:** pytest-dev/pytest  
**Author:** RonnyPfannschmidt  
**Branch:** main <- fix/14528-capture-closed-tmpfile

## PR Description

> ## Summary
>
> Fixes #14528 — `ValueError: I/O operation on closed file` during capture teardown on Windows + Python 3.14.3.
>
> Guards `FDCapture.snap()` and `FDCaptureBinary.snap()` against a prematurely closed `tmpfile`, returning `EMPTY_BUFFER` and emitting a `PytestWarning` instead of crashing. The captured data is unrecoverable regardless, so crashing only makes things worse.
>
> ## Reproduction attempts
>
> The issue was reported on Windows 11 + Python 3.14.3 + pytest 9.0.3 with `pytest-asyncio`, `anyio`, and `pytest-httpx`. Collection short-circuits inside a dot-prefix path (`.claude/skills/actionmail/tests/`) with import errors, and the capture tmpfile is already closed by the time `snap()` runs.
>
> We attempted to reproduce on Windows CI with:
> - Python 3.14.3 (incremental GC active, `gc.get_threshold() = (2000, 10, 0)`)
> - The reporter's exact plugin set (`pytest-asyncio==1.3.0`, `anyio==4.13.0`, `pytest-httpx==0.36.2`)
> - An identical dot-prefix tree layout with `__init__.py`, two test files with `sys.path.insert` + failed `import run`, and a `fixtures/` sibling
>
> **The issue did not reproduce.** All `EncodedFile.close()` calls traced to explicit teardown paths (`pytest_keyboard_interrupt → stop_global_capturing → done → tmpfile.close()`). No GC-triggered file closure was observed. The trigger appears to depend on additional environmental factors specific to the reporter's machine.
>
> Notably, Python 3.14.5 (which reverts the incremental GC) also showed no issue, consistent with the reporter's observation that the problem is 3.14-specific.
>
> ## Changes
>
> - `src/_pytest/capture.py`: Guard `snap()` in both `FDCapture` and `FDCaptureBinary` — check `self.tmpfile.closed` before seeking, emit `PytestWarning`, return `EMPTY_BUFFER`
> - `testing/test_capture.py`: Parametrized regression test using `os.pipe()` for isolation
> - `changelog/14528.bugfix.rst`: Changelog entry
>
> ## Test plan
>
> - [x] Regression test `TestFDCaptureClosedTmpfile` — deterministically closes tmpfile before `snap()`, asserts `EMPTY_BUFFER` and `PytestWarning`
> - [x] Existing capture tests pass
> - [x] Windows CI with Python 3.14.3 + reporter's plugins — no crash (exit code 2)
> - [x] Pre-commit clean

## Changed Files

| File | Changes |
|------|---------|
| [+] changelog/14528.bugfix.rst | +1/-0 |
| [M] src/_pytest/capture.py | +24/-0 |
| [M] testing/test_capture.py | +34/-0 |

## Summary

本次 PR 修复了在 Windows + Python 3.14.3 环境下，捕获机制因临时文件被提前关闭而抛出 `ValueError` 导致崩溃的问题。核心改动是在 `FDCapture.snap()` 和 `FDCaptureBinary.snap()` 方法中增加了对 `tmpfile` 关闭状态的检查，若文件已关闭则返回空缓冲区并发出 `PytestWarning` 而非直接崩溃。涉及 `src/_pytest/capture.py` 的防御性逻辑增强，以及 `testing/test_capture.py` 中新增的回归测试用例。该修复属于局部安全加固，无 API 变更或大范围重构风险。

## Context

本次 PR 修复了 Windows + Python 3.14.3 环境下 `FDCapture.snap()` 因 `tmpfile` 被提前关闭而抛出 `ValueError: I/O operation on closed file` 的崩溃问题，通过守卫检查 `self.tmpfile.closed` 并返回 `EMPTY_BUFFER` 及发出 `PytestWarning` 来避免崩溃，因为此时捕获数据已不可恢复。涉及的核心模块 `src/_pytest/capture.py` 和测试文件 `testing/test_capture.py` 均由 Fridayworks 维护（最后修改于 2026-05-23）。文档层面仅新增了 `changelog/14528.bugfix.rst` 变更日志条目，无需修改用户文档。

## Risk Findings

| File | Line | Type | Description | Suggestion | Confidence |
|------|------|------|-------------|------------|------------|
| src/_pytest/capture.py | 571 | 资源泄漏 | 在 snap() 方法中，当 tmpfile 已关闭时，直接返回 EMPTY_BUFFER，但未处理可能已打开的其他资源（如文件描述符）。虽然当前代码中 tmpfile 关闭后资源已释放，但若未来扩展增加其他资源，此处的提前返回可能导致资源泄漏。 | 确保在提前返回前释放所有已获取的资源，或考虑在 finally 块中统一清理。 | 🟢 不太可能 |
| src/_pytest/capture.py | 571 | 错误处理 | 当 tmpfile 已关闭时，snap() 方法发出警告并返回空缓冲区，但未记录异常或错误上下文。如果 tmpfile 关闭是由于其他未预期的原因（如编程错误），此行为可能掩盖问题，导致调试困难。 | 考虑在警告中增加更多上下文信息，如记录日志或抛出更具体的异常（如 RuntimeError），以便于调试。 | 🟡 可能 |
| src/_pytest/capture.py | 571 | 并发问题 | tmpfile 的关闭状态检查与后续操作（seek、read）之间可能存在竞态条件。如果多个线程同时调用 snap()，一个线程可能检查到 tmpfile 未关闭，但另一个线程随后关闭它，导致第一个线程在已关闭的文件上执行 seek 或 read 操作，引发异常。 | 使用锁（如 threading.Lock）保护对 tmpfile 的访问，或使用原子操作检查并操作文件。 | 🟡 可能 |

## Test Code Risks

| File | Line | Type | Description | Suggestion | Confidence |
|------|------|------|-------------|------------|------------|
| testing/test_capture.py | 1155 | 资源泄漏 | 在 test_snap_returns_empty_on_closed_tmpfile 测试中，pipe_fd fixture 创建了一个管道文件描述符，但在测试中 cap.tmpfile.close() 关闭了 tmpfile，而 cap.done() 可能不会再次关闭该文件描述符，导致文件描述符泄漏。 | 确保在测试结束后正确关闭所有文件描述符，例如在 cap.done() 中处理或使用 try/finally 块。 | 🟠 很可能 |

## Review Suggestions

| File | Line | Category | Description | Confidence |
|------|------|----------|-------------|------------|
| src/_pytest/capture.py | 571 | 代码可读性 | 警告消息中的版本范围 '3.14.0-3.14.4' 和 '3.14.5+' 是硬编码的，未来需要手动更新。建议提取为常量或从外部配置读取，以提高可维护性。 | 🟠 很可能 |
| src/_pytest/capture.py | 571 | 最佳实践 | 警告消息中包含了具体的 Python 版本和 GC 问题细节，这可能导致用户困惑（如果问题在其他版本出现）。建议使用更通用的描述，例如 'capture tmpfile was closed before snap() -- captured output may be lost (possible resource cleanup issue)'，并建议用户报告 bug 而非指定版本。 | 🟡 可能 |
| src/_pytest/capture.py | 571 | 性能 | 在 snap() 方法中每次调用都检查 tmpfile.closed 并可能发出警告，这引入了轻微的性能开销。虽然影响很小，但可以考虑在 start() 或 done() 中设置一个标志位，避免重复检查。 | 🟢 不太可能 |
| src/_pytest/capture.py | 571 | 可维护性 | FDCaptureBinary 和 FDCapture 类中的 snap() 方法有完全相同的 tmpfile.closed 检查逻辑，导致代码重复。建议将检查逻辑提取到父类 FDCaptureBase 的 snap() 方法中，或者创建一个私有辅助方法。 | 🔴 确定 |

## Test Code Suggestions

| File | Line | Category | Description | Confidence |
|------|------|----------|-------------|------------|
| testing/test_capture.py | 1132 | 最佳实践 | 测试类 TestFDCaptureClosedTmpfile 使用了 os.pipe() 创建文件描述符，但 pipe_fd fixture 中关闭了读端 (r)，只保留写端 (w)。这可能导致测试不够直观，建议使用更简单的临时文件或 mock 来模拟关闭的 tmpfile。 | 🟡 可能 |
| testing/test_capture.py | 1148 | 代码可读性 | 测试方法 test_snap_returns_empty_on_closed_tmpfile 中直接访问了 cap.tmpfile 并调用 close()，这破坏了封装性。建议在 capture 类中添加一个 close_tmpfile() 方法或使用 mock 来模拟关闭行为。 | 🟠 很可能 |
| testing/test_capture.py | 1152 | 可维护性 | 测试中使用了 pytest.warns(pytest.PytestWarning, ...) 来断言警告，但警告消息中的版本信息是硬编码的。如果未来修改了警告消息，测试会失败。建议使用 match 参数匹配更通用的部分，或者将警告消息定义为常量并在测试中引用。 | 🟠 很可能 |
