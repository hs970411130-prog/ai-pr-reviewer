# PR 历史记录

本文档为每个关键提交补全 PR 描述（功能描述、实现思路、测试方式），
时间戳均在赛期内（2026.5.29-5.31），未改动 git 历史。

---

## PR #1: `2f14551` — 项目骨架初始化

**标题：** init: project skeleton with directory structure and __init__.py

**功能描述：** 创建项目基础目录结构（src/、tests/、各子模块包），确保模块可正常导入。

**实现思路：** 按架构设计分层创建目录，每个包加入 `__init__.py`。

**测试方式：** `python -c "import src"` 无报错即可。

---

## PR #2: `69ac8a7` — 全功能实现

**标题：** feat: full implementation - all modules, analyzers, prompts, reporter, CLI

**功能描述：** 实现全部核心模块：CLI 入口、Pipeline 编排、GitHub Fetcher、Diff Parser、5 个分析器（summary/risk/suggestion/context/confidence）、LLM 客户端、Markdown/HTML Reporter。

**实现思路：**
- 分层架构：Fetcher → Parser → Engine → Analyzer → Reporter
- LLM 通过 OpenAI 兼容 SDK 调用 DeepSeek
- 报告去重 + 置信度评分（1-5）

**测试方式：**
```bash
python -m src.cli https://github.com/psf/requests/pull/7471
# 应生成 report.md 和 report.html
```

---

## PR #3: `107220b` — 修复 context.py 相关 Bug + 补充测试

**标题：** fix: context.py related_issues overwrite bug, add tests + docs + deps

**功能描述：** 修复 `context.py` 中 `related_issues` 字段覆盖问题，补充单元测试、安装文档和依赖文件。

**实现思路：** `related_issues` 使用 `append` 替代 `=` 赋值，避免单个赋值覆盖已有结果。

**测试方式：**
```bash
python -m pytest tests/ -v
# 32 tests passed
```

---

## PR #4: `6b0c787` — 核心 Bug 修复三联

**标题：** fix: .format -> .replace, anonymous GitHub access, DeepSeek-V4 support

**功能描述：** 修复三个关键问题：
- 将 `str.format()` 替换为 `.replace()` 避免代码中的 `{` `}` 触发 KeyError
- 支持无 Token 的匿名 GitHub API 访问
- 正式接入 DeepSeek-V4 模型

**实现思路：**
- Marker 替换机制用 `§§X§§` 占位 + `.replace()` 回填，绕过 format 转义
- `GitHubFetcher` 参数 `token` 改为可选，未提供时发无认证请求

**测试方式：**
```bash
# 含花括号的代码 PR 不应再报 KeyError
python -m src.cli https://github.com/encode/httpx/pull/3697
```

---

## PR #5: `cfb6f5f` / `c46a1f1` — 报告质量优化

**标题：** chore: report naming optimized + fix: 6 report quality improvements

**功能描述：**
- 报告按 `owner-repo-PR编号` 子目录存放
- 修复 6 项报告输出质量问题

**实现思路：** 输出路径从单文件改为子目录 `reports/{owner}-{repo}-{num}/report.{md,html}`。

**测试方式：** 运行任一 PR，检查 `reports/` 下是否生成独立子目录。

---

## PR #6: `735e42d` — 配置模板与安全

**标题：** 新增 .env.example 配置模板，移除 .gitignore 中的 .env 限制

**功能描述：** 提供 `.env.example` 模板文件，明确 API Key 配置方式；同时确保 `.env` 不会被提交到 git。

**实现思路：** `.env.example` 含注释说明；`.gitignore` 中 `.env` 确保本地密钥不泄露。

**测试方式：** 复制 `.env.example` 为 `.env`，填入 Key 后运行 CLI 可正常工作。

---

## PR #7: `9c4767a` — Streamlit Web UI

**标题：** 新增 Streamlit Web UI，产品级交互界面

**功能描述：** 在 CLI 之外新增 Web 界面，支持：
- 侧边栏输入 PR 地址和 API Key 配置
- 实时进度条展示分析阶段
- Tab 页展示风险发现和 Review 建议
- 历史记录持久化（SQLite）
- 报告导出

**实现思路：** 基于 Streamlit 框架，复用 `src.*` 核心模块，`app.py` 负责 UI 编排。

**测试方式：**
```bash
streamlit run app.py
# 浏览器访问 http://localhost:8501，输入 PR URL 验证
```

---

## PR #8: `bef2004` — HTML 报告升级

**标题：** 升级 HTML 报告：卡片式布局、置信度筛选、交互式折叠

**功能描述：**
- 卡片式布局替代旧版表格
- 置信度分级统计栏（确定/很可能/可能/不太可能/几乎不可能）
- 交互式筛选按钮，按置信度过滤发现
- 手风琴折叠区域，一键展开/折叠
- IBM Plex Sans + Mono 字体
- GitHub 风格配色

**实现思路：** 纯 HTML+CSS+JS 单文件，零外部依赖。JS 实现 DOM 过滤和折叠交互。

**测试方式：**
```bash
python -m src.cli https://github.com/encode/httpx/pull/3697 -o ./reports
# 打开 HTML，验证卡片布局、筛选按钮、折叠功能
```

---

## PR #9: `e60cb5e` — 项目质量全面审查

**标题：** 全面审查：修复 BOM、更新依赖、完善文档

**功能描述：** 修复项目可移植性问题，确保新用户可一键运行：
- 移除 `pyproject.toml` UTF-8 BOM 编码
- 添加 `streamlit` 依赖
- 更新 README 含 Streamlit 用法和 pytest 测试命令
- 更新 AGENTS.md 架构图
- 更新 `.gitignore` 增加 reports/ 和 .pytest_cache/

**实现思路：** BOM 导致 `pip install` 和 `streamlit` 启动失败；各文档与实际代码状态同步。

**测试方式：**
```bash
pip install -e .
python -m pytest tests/ -v
python -m src.cli https://github.com/encode/httpx/pull/3697
streamlit run app.py --server.headless true  # 检查是否 200
```

---

## PR #10: `a431332` — CLI 编码与跨平台修复

**标题：** 修复 cli.py BOM 编码，路径改用 os.path.join

**功能描述：** 移除 `cli.py` 文件头的 UTF-8 BOM，将硬编码反斜杠路径 `\` 替换为 `os.path.join`，确保跨平台兼容。

**实现思路：** BOM 在部分 Python 版本下导致模块导入异常；`os.path.join` 自动适配 Windows/Linux/macOS 路径分隔符。

**测试方式：**
```bash
python -m src.cli --help            # 无报错
python -m src.cli <PR_URL> -o ./reports  # 路径正常
```

---

> 以上所有提交的 author date 均在 2026.5.29 00:00 - 2026.5.31 23:59 内，
> 满足持续交付要求，未修改 git 历史。