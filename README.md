# AI PR Review 助手

自动分析 GitHub Pull Request 的 AI 代码评审工具。指定 PR URL，一键获取变更摘要、风险识别和 Review 建议。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
set DEEPSEEK_API_KEY=your_deepseek_api_key
set GITHUB_TOKEN=your_github_token

# 3. 运行分析
python -m src.cli https://github.com/owner/repo/pull/42
```

## 功能

- **PR 变更总结** — 3-5 句中文摘要，概述本次 PR 的目的和改动范围
- **风险代码识别** — 检测安全漏洞、空指针、并发问题、资源泄漏等，每条带置信度评分
- **Review 建议生成** — 针对代码可读性、性能、最佳实践提出具体改进建议
- **上下文增强** — 关联 Issue 引用、git blame 信息、文档变更分析
- **误报控制** — 每条发现带 1-5 置信度评分，去重，低置信度标注"待人工确认"
- **双格式报告** — 同时输出 Markdown 和单文件 HTML

## 用法

```bash
# 基本用法
python -m src.cli https://github.com/owner/repo/pull/42

# 指定输出目录
python -m src.cli https://github.com/owner/repo/pull/42 -o ./reports

# 通过 CLI 传入 GitHub Token
python -m src.cli https://github.com/owner/repo/pull/42 --github-token ghp_xxx
```

## 项目结构

```
src/
├── cli.py              # CLI 入口
├── pipeline.py         # 全链路编排
├── models.py           # 数据模型
├── config/settings.py  # 集中配置
├── fetcher/            # GitHub API 数据获取
├── parser/             # Diff 结构化解析
├── analyzer/           # 分析引擎 + 5 个分析器
├── llm/                # LLM 客户端 + Prompt 模板
└── reporter/           # 报告生成 + 置信度评分
```

## 设计思路

### 模型选择

选用 **DeepSeek-V3（deepseek-chat）**：

- **成本低** — API 价格约为 GPT-4o 的 1/10，单次 PR 分析仅几分钱
- **中文好** — 中文理解和生成质量优秀，Review 建议表达自然
- **兼容性强** — 完全兼容 OpenAI API 协议，通过 `openai` SDK 调用，LLM 抽象层（`llm/client.py`）只需修改 `LLM_API_BASE` 和 `LLM_MODEL` 配置即可切换到其他 OpenAI 兼容服务

### 上下文获取方式

系统通过以下途径获取 PR diff 之外的上下文：

1. **关联 Issue** — 从 PR body 中提取 `#123` 格式的 Issue 引用
2. **git blame** — 通过 GitHub API 查询变更文件的主要维护者，帮助评审者了解代码归属
3. **文档变更感知** — 识别 `.md` 等文档文件的变更，辅助理解 PR 的业务背景

### 未来扩展方向

架构设计支持以下方向的扩展：

- **多模型支持** — `llm/client.py` 通过配置切换，可接入 OpenAI、Claude、豆包等
- **多平台** — `fetcher/base.py` 抽象接口，新增 `gitlab.py` / `gitee.py` 即可扩展
- **增量分析** — Engine 分批策略已支持按文件调度，可扩展为增量 review（只分析新增 commit）
- **自定义规则** — Prompt 模板（`llm/prompts/`）独立于代码，评审规则可灵活调整
- **CI 集成** — Pipeline 设计为无状态函数，可直接嵌入 GitHub Actions / GitLab CI

## 技术栈

| 组件 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| LLM | DeepSeek-V3 |
| LLM SDK | openai |
| HTTP | httpx |
| CLI | click |
| Web UI | 纯 HTML 单文件 |

## 运行测试

```bash
python -m unittest discover -s tests -v
```
