# PRODUCT.md

## Project

AI PR Review 助手 — 自动分析 GitHub Pull Request 的 AI 代码评审工具。

## Register

product

## Target Users

需要提升 PR Review 效率的开发者与团队 Tech Lead。

## Purpose

借助 AI 自动完成 PR 代码风险检测、内容总结与评审建议输出，大幅缩减人工评审耗时，同时提升代码问题检出质量。用户在输入 GitHub PR 链接后 3 分钟内获得结构化的 Review 报告。

## Brand Personality

专业、智能、高效

- **专业**：评审结果严谨可靠，信息层级清晰，问题分类遵从行业标准
- **智能**：AI 能力自然融入工作流，分析过程透明可追踪
- **高效**：零学习成本，一键分析，结果直达关键发现

## References

### Positive (aspirational)
- **GitHub Pull Requests**：极简布局、信息层级清晰，贴合开发者习惯，无多余视觉元素
- **GitHub Copilot**：交互克制、功能聚焦，AI 能力自然融入，提示简洁不打扰
- **Snyk**：风险分级明确、告警直观，问题标注与分类逻辑专业，突出风险优先级

### Anti (avoid)
- 拒绝过度花哨动效、冗余装饰元素，不做娱乐化视觉设计
- 拒绝布局杂乱、信息堆砌的传统管理后台风格
- 拒绝晦涩的极客暗黑风格、非标准化交互，新手可快速上手

## Strategic Design Principles

1. **信息为王** — 评审结果是核心价值，UI 让位内容；不抢戏、不装饰、不showoff
2. **渐进披露** — 摘要优先，风险和建议可展开，避免信息轰炸
3. **开发者直觉** — 布局、字体、间距、配色对标 GitHub 生态，用户无需学习
4. **信任透明** — 每条 AI 发现标注置信度，区分"确定"与"可能"，建立可信度
5. **一键到底** — 输入 PR URL → 获得报告，中间不打断、不要求多步确认

## Stack

- **Frontend**: Streamlit
- **Backend**: Python (CLI + Pipeline)
- **LLM**: DeepSeek-V4（OpenAI 兼容协议）
- **API**: GitHub REST API
