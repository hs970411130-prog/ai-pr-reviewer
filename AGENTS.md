# AGENTS.md

## 项目概要

**项目名称：** AI PR Review 助手
**来源：** 七牛云 XEngineer 新工科计划 — 第二批议题（题目三）
**开发周期：** 2026年5月29日 00:00 - 2026年5月31日 23:59（72小时）

---

## 1. 题目要求（不可偏离）

### 功能要求
- [ ] **用户指定 GitHub PR**，系统自动获取代码变更并智能分析
- [ ] **PR 变更总结** — 摘要级别概述本次 PR 做了什么
- [ ] **风险代码识别** — 安全漏洞、空指针、并发问题、资源泄漏等
- [ ] **Review 建议生成** — 具体到行级/文件级的修改建议

### 质量要求
- [ ] **分析准确性** — 分层 Prompt 设计，减少幻觉
- [ ] **上下文理解** — 关联 Issue、文件历史（git blame）、项目结构
- [ ] **误报与漏报控制** — 每条发现带置信度评分（1-5），低置信度标注"待人工确认"
- [ ] **响应速度** — 分析模块可并行调用，不串行阻塞
- [ ] **使用体验** — CLI 一键分析 + 单文件 HTML 报告

### 设计说明要求（须在 README 中明确）
- [ ] **模型选择的设计思路** — 为什么选 DeepSeek，如何切换
- [ ] **上下文获取方式的设计思路** — 如何拿到 PR 之外的上下文
- [ ] **未来扩展方向的设计思路** — 架构如何支持扩展

### 边界（不做）
- 不做通用代码扫描工具
- 不做本地项目代码检查
- 不自动 merge / close PR
- 定位是**辅助 Review，不是替代人工** — 给出建议但标注置信度

---

## 2. 行为准则（继承自 CLAUDE.md）

### 2.1 先想再做
- 实现前明确说出你的假设。不确定就问。
- 存在多种解读时，列出选项而非沉默选择。
- 存在更简单的方案时，指出来。

### 2.2 简洁优先
- 只写解决问题所需的最少代码。不加未要求的功能。
- 不复用就抽象的单一场景代码 — 不要。
- 不求"灵活"、"可配置"除非需求明确要求。
- 不为不可能发生的场景做错误处理。

### 2.3 外科手术式修改
- 只动必须改的地方。不顺手"优化"相邻代码。
- 不改不相关的东西，包括注释、格式。
- 匹配现有风格。
- 自己的改动造成的死代码要清理，但不碰已有的死代码。

### 2.4 目标驱动
- 把任务转化为可验证目标，每步带验证条件。

---

## 3. 架构

### 项目结构
```
ai-pr-reviewer/
├── app.py                 # Streamlit Web UI
├── .streamlit/            # Streamlit 配置

│   ├── __init__.py
│   ├── cli.py              # CLI 入口（click），只做参数解析
│   ├── pipeline.py         # 全链路编排：Fetcher → Parser → Engine → Reporter
│   ├── models.py           # 数据模型：FileChange, AnalysisResult, RiskFinding 等
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py     # 集中配置：过滤后缀、分批参数、LLM 参数
│   ├── fetcher/
│   │   ├── __init__.py
│   │   ├── base.py         # 抽象接口
│   │   └── github.py       # GitHub REST API 实现
│   ├── parser/
│   │   ├── __init__.py
│   │   └── diff_parser.py  # Unified diff → [FileChange]（不过滤，保留全量）
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── engine.py       # 过滤 + 分批 + 调度 LLM 调用
│   │   ├── summary.py      # PR 变更总结
│   │   ├── risk.py         # 风险代码识别
│   │   ├── suggestion.py   # Review 建议生成
│   │   └── context.py      # 上下文增强（内部拆分：拉取数据 + LLM 分析）
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py       # OpenAI 兼容客户端（DeepSeek），含 _load_prompt()
│   │   └── prompts/
│   │       ├── summary.md
│   │       ├── risk.md
│   │       ├── suggestion.md
│   │       └── context.md
│   └── reporter/
│       ├── __init__.py
│       ├── confidence.py   # 去重 + 置信度评分
│       ├── markdown.py     # Markdown 报告
│       └── web.py          # 单文件 HTML 报告
├── tests/
├── AGENTS.md
└── README.md
```

### 技术选型
| 组件 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| LLM | DeepSeek-V4（`deepseek-chat`），OpenAI 兼容协议 |
| LLM SDK | `openai` 包 |
| HTTP | `httpx` |
| CLI | `click` |
| Web UI | Streamlit + 纯 HTML 单文件 |
| GitHub API | REST API，Token 认证 |

### 核心数据流
```
CLI（PR URL）
  → Pipeline 编排
    → Fetcher 获取 PR 元数据 + diff
      → Parser 切分为 [FileChange]（全量，不过滤）
        → Engine 按 Analyzer 类型过滤 + 分批
          → 并行调 LLM 分析
            → Reporter 聚合 + 去重 + 置信度
              → 输出 Markdown + HTML
```

### 分块策略（Engine 层）
1. Parser 不做过滤，保留全量
2. Engine 按 Analyzer 类型决策：
   - Summary：全量文件列表（含配置/文档）
   - Risk / Suggestion：只送代码文件
   - Context：可读文档变更 + git blame
3. 分批：1~3 文件/批，单文件 ≤10000 字符，不截断
4. 跳过后缀：`.md .txt .rst .json .yaml .yml .toml .lock .svg .png .jpg .ico .gitignore`
5. 跳过策略集中在 `config/settings.py` 的 `SKIP_EXTENSIONS`

---

## 4. 运行时配置

### LLM（`config/settings.py`）
| 配置项 | 值 | 来源 |
|--------|-----|------|
| API Base | `https://api.deepseek.com` | 硬编码 |
| 模型 | `deepseek-chat` | 硬编码 |
| API Key | `DEEPSEEK_API_KEY` | 环境变量 |
| Temperature | 0.1 | |
| Max Tokens | 4096 | |

### GitHub
| 配置项 | 来源 | 优先级 |
|--------|------|--------|
| Token | `GITHUB_TOKEN` 环境变量 | 优先 |
| Token | `--github-token` CLI 参数 | 备用 |

---

## 5. 开发流程

### 开发顺序（按依赖）
1. 项目骨架：`git init` + 目录 + `__init__.py` + `models.py` + `config/settings.py`
2. `fetcher/github.py` — 能拿到真实 PR 数据
3. `parser/diff_parser.py` — 结构化 diff
4. `llm/client.py` + `analyzer/engine.py` — 打通 LLM + 分块
5. `analyzer/summary.py` — 第一个 Analyzer，验证全链路
6. 其余 Analyzer 逐个实现
7. `reporter/` — 报告输出
8. `pipeline.py` + `cli.py` — 串联入口
9. `README.md` — 含模型/上下文/扩展的设计思路

### Git 规范（评审规则强制）
- 每个 commit/PR 只做一件事
- PR 描述：标题 + 功能描述 + 实现思路 + 测试方式
- 持续交付，严禁最后一天突击
- 主分支始终保持可运行

### 测试策略
- 每个模块至少一个测试
- Fetcher 用 mock GitHub API
- LLM 用 mock response
- 集成测试用真实开源 PR

---

## 6. 禁止事项

- ❌ 偏离题目范围
- ❌ 过度设计（不加未要求的抽象层）
- ❌ 引入重依赖（不用 Django/Flask/FastAPI）
- ❌ 声称支持但未实现（如 GitLab/Gitee）
- ❌ 最后一天突击提交
- ❌ 截断代码行送 LLM
- ❌ Parser 层做过滤
- ❌ 忘记在 README 中写设计思路
