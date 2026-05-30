# AI PR Review 助手 — 演示视频脚本

> 预计时长：5-8 分钟 | 建议使用 OBS 录屏 + 系统音频

---

## 一、项目简介（30 秒）

**画面：** GitHub 仓库首页 + README.md
**讲解：**
"AI PR Review 助手，一个自动分析 GitHub Pull Request 的 AI 代码评审工具。
输入 PR 链接，一键获取变更摘要、风险识别和 Review 建议。
支持 CLI 命令行和 Streamlit Web 界面两种模式。"

---

## 二、快速开始（40 秒）

**画面：** 终端操作
```bash
git clone https://github.com/hs970411130-prog/ai-pr-reviewer.git
cd ai-pr-reviewer
pip install -e .
cp .env.example .env
```

**讲解：**
"克隆仓库后 pip install 即可安装。复制 .env.example 为 .env，
填入 DeepSeek API Key 和 GitHub Token 即可使用。现已支持 --version 查看版本。"

**画面：** 
```bash
python -m src.cli --version
# ai-pr-reviewer v0.1.0
```

---

## 三、CLI 模式演示（1.5 分钟）

**画面：** 终端
```bash
python -m src.cli https://github.com/encode/httpx/pull/3697
```

**讲解：**
"CLI 模式下只需要一行命令。系统会自动：
- 拉取 PR 元数据和 diff
- 调用 DeepSeek-V4 进行代码分析
- 输出摘要、风险发现和 Review 建议
- 生成 Markdown 和 HTML 双格式报告

注意控制台实时输出：分析中、风险发现条数、建议条数。"

---

## 四、HTML 报告展示（1.5 分钟）

**画面：** 浏览器打开 HTML 报告
**讲解：**
"HTML 报告是产品级交互式设计：

- **顶部统计栏** — 按置信度分级展示：确定、很可能、可能、不太可能
- **筛选按钮** — 点击切换置信度级别，动态过滤下方的发现列表
- **手风琴折叠** — 风险发现、测试代码风险、Review 建议分类展示，点击展开/折叠
- **一键折叠** — 全部折叠按钮，快速总览结构
- **GitHub 风格配色** — IBM Plex 字体，对标 GitHub 设计语言

每条发现标注：文件名、行号、风险类型、置信度徽章、具体建议。"

---

## 五、Streamlit Web UI 演示（1.5 分钟）

**画面：** 浏览器 http://localhost:8501
```bash
streamlit run app.py
```

**讲解：**
"Web 界面提供更友好的交互体验：

- **侧边栏** — 输入 PR 地址和 API Key 配置（自动持久化）
- **PR 预览卡片** — 提交后自动展示 PR 信息
- **进度条** — 实时展示分析阶段：拉取数据 → 分析中 → 生成报告
- **Tab 页** — 风险发现 / Review 建议分 Tab 展示
- **历史记录** — SQLite 持久化，可回溯过往分析
- **导出按钮** — 一键下载 HTML 报告"

---

## 六、核心架构（1 分钟）

**画面：** 切换回 README 项目结构图
**讲解：**
"架构分为六层：

- **Fetcher 层** — GitHub API 数据获取，抽象接口支持扩展 GitLab/Gitee
- **Parser 层** — Unified diff 结构化解析
- **Analyzer 层** — 五个分析器：Summary 摘要、Risk 风险识别、Suggestion 建议、Context 上下文增强、Confidence 置信度评分
- **LLM 层** — OpenAI 兼容客户端，当前接入 DeepSeek-V4，可切换其他模型
- **Reporter 层** — Markdown + 单文件 HTML 双格式报告
- **Pipeline 层** — 全链路编排，支持并行调用

LLM Prompts 独立存放，评审规则可灵活调整。CLI 与 Web UI 共享同一 Pipeline。"

---

## 七、测试与质量（30 秒）

**画面：** 终端运行 pytest
```bash
pytest tests/ -v
```

**讲解：**
"32 个单元测试覆盖全部核心模块：fetcher、parser、engine、summary、risk、suggestion、confidence、models。
集成测试可直接用真实开源 PR 验证。所有提交遵循 PR 规范：一功能一分支，完整描述，合并后主分支始终保持可运行。"

---

## 八、结尾（20 秒）

**画面：** 仓库首页 + Star 按钮
**讲解：**
"AI PR Review 助手，让代码评审更高效。欢迎 Star 和 PR 贡献！"