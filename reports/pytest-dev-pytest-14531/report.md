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

本次 PR 修复了在 Windows + Python 3.14.3 环境下，捕获机制因临时文件提前关闭而崩溃的问题。核心改动是在 `FDCapture.snap()` 和 `FDCaptureBinary.snap()` 方法中增加了对 `tmpfile` 关闭状态的检查，若文件已关闭则返回空缓冲区并发出 `PytestWarning` 而非抛出异常。涉及的主要模块为 `src/_pytest/capture.py`，并新增了回归测试用例。该修复属于防御性编程，未引入 API 变更或大范围重构，风险较低。

## Context

本次 PR 修复了 Windows + Python 3.14.3 环境下 `FDCapture.snap()` 因 `tmpfile` 被提前关闭而抛出 `ValueError: I/O operation on closed file` 的崩溃问题，通过守卫检查 `self.tmpfile.closed` 并返回 `EMPTY_BUFFER` 及发出 `PytestWarning` 来避免崩溃，因为捕获数据已不可恢复。涉及的核心模块 `src/_pytest/capture.py` 和测试文件 `testing/test_capture.py` 均由 Fridayworks 维护（最后修改于 2026-05-23）。文档层面新增了 `changelog/14528.bugfix.rst` 变更日志条目，无需修改用户文档。

## Risk Findings

| File | Line | Type | Description | Suggestion | Confidence |
|------|------|------|-------------|------------|------------|
| src/_pytest/capture.py | 571 | 资源泄漏 | 在 snap() 方法中，如果 tmpfile 已关闭，直接返回 EMPTY_BUFFER，但未处理可能已打开的文件描述符或资源。虽然 tmpfile 已关闭，但 snap() 方法可能在其他上下文中被调用，导致资源状态不一致。 | 确保在返回前清理所有相关资源，或记录更详细的错误信息以便调试。 | 🟢 不太可能 |
| src/_pytest/capture.py | 571 | 错误处理 | 当 tmpfile 已关闭时，仅发出警告并返回空缓冲区，但未处理可能存在的其他错误状态（如 tmpfile 为 None 或无效）。这可能导致静默数据丢失。 | 考虑在警告后抛出异常或记录更详细的错误，以便调用者知晓捕获输出已丢失。 | 🟡 可能 |
| src/_pytest/capture.py | 604 | 资源泄漏 | 与 FDCaptureBinary.snap() 类似，在 FDCapture.snap() 中，如果 tmpfile 已关闭，直接返回 EMPTY_BUFFER，但未处理可能已打开的文件描述符或资源。 | 确保在返回前清理所有相关资源，或记录更详细的错误信息以便调试。 | 🟢 不太可能 |
| src/_pytest/capture.py | 604 | 错误处理 | 当 tmpfile 已关闭时，仅发出警告并返回空缓冲区，但未处理可能存在的其他错误状态（如 tmpfile 为 None 或无效）。这可能导致静默数据丢失。 | 考虑在警告后抛出异常或记录更详细的错误，以便调用者知晓捕获输出已丢失。 | 🟡 可能 |

## Test Code Risks

| File | Line | Type | Description | Suggestion | Confidence |
|------|------|------|-------------|------------|------------|
| testing/test_capture.py | 1145 | 资源泄漏 | 在 pipe_fd fixture 中，如果 os.close(w) 抛出 OSError，异常被捕获并忽略，但可能掩盖了其他资源清理问题。此外，如果 yield 之前发生异常，写端可能未关闭。 | 考虑使用 try/finally 确保写端始终被关闭，或记录忽略的异常以便调试。 | 🟡 可能 |

## Review Suggestions

| File | Line | Category | Description | Confidence |
|------|------|----------|-------------|------------|
| src/_pytest/capture.py | 571 | 最佳实践 | 警告消息中包含了具体的Python版本范围（3.14.0-3.14.4），这会导致代码与特定版本强耦合。建议改为更通用的描述，例如 'likely caused by Python incremental GC bug in some versions'，或者将版本信息作为可配置参数，以便未来更新。 | 🟠 很可能 |
| src/_pytest/capture.py | 571 | 代码可读性 | 警告消息过长且包含技术细节，可能对用户造成困惑。建议拆分为更简洁的警告，并建议用户查看文档或升级Python，而不是在消息中列出具体版本。 | 🟡 可能 |
| src/_pytest/capture.py | 571 | 性能 | 在snap()方法中每次调用都检查tmpfile.closed，虽然开销很小，但考虑到snap()可能被频繁调用，建议在FDCaptureBase的__init__或start()中缓存tmpfile状态，或者使用一个标志位来避免重复检查。 | 🟢 不太可能 |
| src/_pytest/capture.py | 571 | 可维护性 | FDCaptureBinary和FDCapture类中的snap()方法有重复的tmpfile.closed检查逻辑。建议将检查逻辑提取到FDCaptureBase基类中的公共方法，例如_check_tmpfile_closed()，以减少代码重复并提高可维护性。 | 🔴 确定 |

## Test Code Suggestions

| File | Line | Category | Description | Confidence |
|------|------|----------|-------------|------------|
| testing/test_capture.py | 1132 | 最佳实践 | 测试类TestFDCaptureClosedTmpfile使用了os.pipe()创建文件描述符，但pipe_fd fixture中关闭了读端(r)，只保留写端(w)。这可能导致测试不够直观，因为写端在测试中并未实际使用。建议直接使用一个临时文件或模拟对象来测试tmpfile关闭场景，以提高测试的可读性和可靠性。 | 🟡 可能 |
| testing/test_capture.py | 1148 | 代码可读性 | 测试方法test_snap_returns_empty_on_closed_tmpfile中，cap.tmpfile.close()直接访问了私有属性tmpfile。虽然这是测试代码，但建议通过公共接口或添加一个辅助方法来关闭tmpfile，以避免测试与实现细节过度耦合。 | 🟠 很可能 |
| testing/test_capture.py | 1150 | 最佳实践 | 测试中使用了pytest.warns(pytest.PytestWarning, ...)来断言警告，但警告消息中的版本信息（3.14.0-3.14.4）可能随Python版本变化而失效。建议使用更通用的匹配模式，例如match='capture tmpfile was closed'，以避免测试因版本更新而失败。 | 🟠 很可能 |
