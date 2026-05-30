"""AI PR Review 助手 — Streamlit Web UI.  产品级终稿布局."""

import sys, os, json, sqlite3
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI PR Review",
    page_icon=":material/rate_review:",
    layout="wide",
)

# ── CSS tweaks ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .st-key-topbar { display: flex; align-items: center; justify-content: space-between; }
    .st-key-topbar h2 { margin: 0; }
    .pr-preview-card { padding: 16px; border: 1px solid #d0d7de; border-radius: 8px; background: #f6f8fa; }
    .pr-preview-card h4 { margin: 0 0 4px 0; }
    .pr-preview-card p { margin: 0; color: #57606a; font-size: 13px; }
    .step-done { color: #1a7f37; }
    .step-active { color: #0969da; font-weight: bold; }
    .step-pending { color: #d0d7de; }
</style>
""", unsafe_allow_html=True)

# ── Init session ───────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "config" not in st.session_state:
    st.session_state.config = {}

# ── SQLite for history persistence ─────────────────────────────────────────
DB_PATH = Path.home() / ".ai-pr-reviewer" / "history.db"


def _init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, repo TEXT, pr_num INTEGER, title TEXT,
            risk_count INTEGER, sug_count INTEGER, date TEXT
        )
    """)
    conn.commit()
    return conn


def _load_history():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT url, repo, pr_num, title, risk_count, sug_count, date FROM history ORDER BY id DESC LIMIT 20"
        ).fetchall()
        return [{"url": r[0], "repo": r[1], "pr_num": r[2], "title": r[3],
                 "risk_count": r[4], "sug_count": r[5], "date": r[6]} for r in rows]
    except Exception:
        return []


def _save_history(url, repo, pr_num, title, risk_count, sug_count):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO history (url, repo, pr_num, title, risk_count, sug_count, date) VALUES (?,?,?,?,?,?,?)",
        (url, repo, pr_num, title, risk_count, sug_count, date.today().isoformat()),
    )
    conn.commit()


_init_db()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — Config only
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### :material/settings: 配置")

    deepseek_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=st.session_state.config.get("deepseek_key", os.getenv("DEEPSEEK_API_KEY", "")),
        key="cfg_key",
    )
    github_token = st.text_input(
        "GitHub Token",
        type="password",
        value=st.session_state.config.get("github_token", os.getenv("GITHUB_TOKEN", "")),
        key="cfg_token",
    )
    model = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-reasoner"],
        index=0,
        key="cfg_model",
    )
    batch_size = st.number_input(
        "每批文件数",
        min_value=1, max_value=10,
        value=st.session_state.config.get("batch_size", 3),
        key="cfg_batch",
    )

    if st.button(":material/save: 保存配置", use_container_width=True):
        st.session_state.config = {
            "deepseek_key": deepseek_key,
            "github_token": github_token,
            "model": model,
            "batch_size": batch_size,
        }
        # Persist to JSON
        config_path = Path.home() / ".ai-pr-reviewer" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(st.session_state.config, indent=2))
        st.toast("配置已保存", icon=":material/check:")

    st.divider()

    # Load persisted config
    config_path = Path.home() / ".ai-pr-reviewer" / "config.json"
    if config_path.exists() and not st.session_state.config:
        try:
            st.session_state.config = json.loads(config_path.read_text())
            st.rerun()
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════════════
# TOP BAR
# ═══════════════════════════════════════════════════════════════════════════
tc1, tc2, tc3 = st.columns([4, 1, 1], vertical_alignment="center")
with tc1:
    st.markdown("## :material/rate_review: AI PR Review")
with tc2:
    dark_mode = st.toggle(":material/dark_mode:", key="dark_toggle")
    if dark_mode:
        st._config.set_option("theme.base", "dark")
with tc3:
    hist_btn = st.button(":material/history: 历史", use_container_width=True, key="hist_btn")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN — PR URL input
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("### :material/link: 输入 GitHub PR 地址")
pr_url = st.text_input(
    "pr_url_input",
    placeholder="https://github.com/owner/repo/pull/42",
    label_visibility="collapsed",
    key="pr_url_input",
)

# ── PR Preview ─────────────────────────────────────────────────────────────
preview_owner = preview_repo = preview_num = None
preview_meta = None

if pr_url:
    try:
        from src.fetcher.github import parse_pr_url
        preview_owner, preview_repo, preview_num = parse_pr_url(pr_url)
        # Try to fetch metadata for preview
        @st.cache_data(show_spinner=False, ttl=60)
        def _preview_meta(owner, repo, num, token):
            from src.fetcher.github import GitHubFetcher
            try:
                f = GitHubFetcher(token=token)
                return f.fetch_metadata(owner, repo, num)
            except Exception:
                return None

        preview_meta = _preview_meta(preview_owner, preview_repo, preview_num, github_token)
    except ValueError:
        pass

if preview_meta:
    with st.container(border=True):
        st.markdown(f"**{preview_meta.title}**")
        st.caption(
            f":material/person: {preview_meta.author}  ·  "
            f":material/git_branch: {preview_meta.base_branch} ← {preview_meta.head_branch}"
        )

# ── Action buttons ─────────────────────────────────────────────────────────
bc1, bc2, bc3 = st.columns([2, 2, 6])
with bc1:
    analyze_clicked = st.button(
        ":material/play_arrow: 开始分析",
        type="primary",
        use_container_width=True,
        disabled=not pr_url,
    )
with bc2:
    batch_clicked = st.button(
        ":material/list: 批量分析",
        use_container_width=True,
        disabled=not pr_url,
        help="粘贴多个 PR URL，每行一个",
    )

# ── Batch mode ─────────────────────────────────────────────────────────────
if batch_clicked:
    urls_text = st.text_area(
        "批量输入 PR URL（每行一个）",
        value=pr_url + "\n",
        height=120,
        key="batch_urls",
    )
    batch_urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
    if st.button(":material/rocket_launch: 开始批量分析", type="primary"):
        for i, url in enumerate(batch_urls):
            st.info(f"正在分析 {i+1}/{len(batch_urls)}: {url}")
            # TODO: queue-based batch processing
            st.caption("批量分析功能开发中...")
            break

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS PIPELINE
# ═══════════════════════════════════════════════════════════════════════════
if analyze_clicked and pr_url:
    if not deepseek_key:
        st.error("请先在左侧配置 DeepSeek API Key")
        st.stop()
    if "pull" not in pr_url:
        st.error("请输入有效的 GitHub PR 地址")
        st.stop()

    os.environ["DEEPSEEK_API_KEY"] = deepseek_key
    os.environ["GITHUB_TOKEN"] = github_token

    from src.fetcher.github import GitHubFetcher, parse_pr_url
    from src.analyzer.engine import run_analysis, filter_code_files, find_skipped_files
    from src.analyzer import summary, risk, suggestion, context
    from src.reporter import confidence, markdown, web
    from src.models import AnalysisReport

    owner, repo, num = parse_pr_url(pr_url)

    # ── Progress steps ──────────────────────────────────────────────────
    st.divider()
    st.markdown("### :material/progress_activity: 分析进度")
    steps = st.columns(5)
    step_labels = ["拉取 PR 数据", "生成摘要", "风险分析", "建议生成", "上下文分析"]
    step_icons = ["download", "summarize", "warning", "lightbulb", "info"]
    step_placeholders = [
        steps[i].markdown(f":gray[:material/{step_icons[i]}:] {step_labels[i]}")
        for i in range(5)
    ]

    progress = st.progress(0)
    status = st.empty()

    try:
        # Step 1: Fetch
        step_placeholders[0].markdown(f":blue[:material/download:] {step_labels[0]}")
        status.info("正在拉取 PR 数据...")
        fetcher = GitHubFetcher(token=github_token)
        meta = fetcher.fetch_metadata(owner, repo, num)
        changes = fetcher.fetch_diff(owner, repo, num)
        progress.progress(20)
        step_placeholders[0].markdown(f":green[:material/check_circle:] {step_labels[0]}")

        # Step 2: Summary
        step_placeholders[1].markdown(f":blue[:material/summarize:] {step_labels[1]}")
        status.info("正在生成摘要...")
        summary_text = summary.summarize(meta, changes)
        progress.progress(45)
        step_placeholders[1].markdown(f":green[:material/check_circle:] {step_labels[1]}")

        # Step 3: Risk
        step_placeholders[2].markdown(f":blue[:material/warning:] {step_labels[2]}")
        status.info("正在分析风险...")
        code_only = filter_code_files(changes)
        risks_raw = run_analysis(code_only, risk.analyze, filter_code=False)
        progress.progress(65)
        step_placeholders[2].markdown(f":green[:material/check_circle:] {step_labels[2]}")

        # Step 4: Suggestions
        step_placeholders[3].markdown(f":blue[:material/lightbulb:] {step_labels[3]}")
        status.info("正在生成 Review 建议...")
        suggestions_raw = run_analysis(code_only, suggestion.analyze, filter_code=False)
        progress.progress(85)
        step_placeholders[3].markdown(f":green[:material/check_circle:] {step_labels[3]}")

        # Step 5: Context
        step_placeholders[4].markdown(f":blue[:material/info:] {step_labels[4]}")
        status.info("正在分析上下文...")
        ctx = context.enhance(meta, changes)
        progress.progress(100)
        step_placeholders[4].markdown(f":green[:material/check_circle:] {step_labels[4]}")
        status.empty()

        # Aggregate
        deduped_risks = confidence.deduplicate_risks(risks_raw)
        deduped_sugs = confidence.deduplicate_suggestions(suggestions_raw)
        report = AnalysisReport(
            pr_metadata=meta, summary=summary_text,
            risks=deduped_risks, suggestions=deduped_sugs,
            context=ctx, file_changes=changes,
            skipped_files=find_skipped_files(changes),
        )

        # Save history
        _save_history(pr_url, f"{owner}/{repo}", num, meta.title,
                      len(deduped_risks), len(deduped_sugs))
        st.toast("分析完成！", icon=":material/check:")

        # ══════════════════════════════════════════════════════════════════
        # RESULTS TABS
        # ══════════════════════════════════════════════════════════════════
        st.divider()
        st.markdown("### :material/description: 分析结果")

        tabs = st.tabs([
            f":material/summarize: 摘要",
            f":material/warning: 风险 ({len(report.risks)})",
            f":material/lightbulb: 建议 ({len(report.suggestions)})",
            f":material/info: 上下文",
            f":material/description: 文件变更",
        ])

        with tabs[0]:
            st.markdown(report.summary)

        with tabs[1]:
            if report.risks:
                st.dataframe(
                    [{"文件": r.file, "行号": r.line, "类型": r.risk_type,
                      "描述": r.description, "建议": r.suggestion,
                      "置信度": confidence.confidence_label(r.confidence)}
                     for r in report.risks],
                    use_container_width=True, hide_index=True,
                    column_config={"置信度": st.column_config.Column(width="small")},
                )
            else:
                st.success("未发现风险")

        with tabs[2]:
            if report.suggestions:
                st.dataframe(
                    [{"文件": s.file, "行号": s.line, "类别": s.category,
                      "描述": s.description,
                      "置信度": confidence.confidence_label(s.confidence)}
                     for s in report.suggestions],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.success("暂无建议")

        with tabs[3]:
            if report.context and report.context.analysis_text:
                st.markdown(report.context.analysis_text)
            else:
                st.caption("无额外上下文信息")

        with tabs[4]:
            st.dataframe(
                [{"文件": fc.filename, "状态": fc.change_type.value,
                  "新增": f"+{fc.additions}", "删除": f"-{fc.deletions}"}
                 for fc in report.file_changes],
                use_container_width=True, hide_index=True,
            )

        # ══════════════════════════════════════════════════════════════════
        # EXPORT BUTTONS
        # ══════════════════════════════════════════════════════════════════
        st.divider()
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            html_report = web.generate(report)
            st.download_button(
                ":material/download: 下载 HTML 报告",
                data=html_report,
                file_name=f"{owner}-{repo}-{num}-report.html",
                mime="text/html",
                use_container_width=True,
            )
        with ec2:
            md_report = markdown.generate(report)
            st.download_button(
                ":material/download: 下载 Markdown",
                data=md_report,
                file_name=f"{owner}-{repo}-{num}-report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with ec3:
            if st.button(":material/content_copy: 复制 Markdown", use_container_width=True):
                st.code(md_report, language="markdown")
                st.toast("已显示 Markdown，Ctrl+C 复制", icon=":material/check:")

        st.session_state.history.append({
            "url": pr_url, "repo": f"{owner}/{repo}", "pr_num": num,
            "title": meta.title, "risk_count": len(deduped_risks),
            "sug_count": len(deduped_sugs), "date": date.today().isoformat(),
        })

    except Exception as e:
        progress.progress(100)
        status.empty()
        st.error(f"分析失败：{e}")

# ═══════════════════════════════════════════════════════════════════════════
# HISTORY SECTION (when history button clicked or always at bottom)
# ═══════════════════════════════════════════════════════════════════════════
if hist_btn or st.session_state.get("show_history", False):
    st.session_state.show_history = not st.session_state.get("show_history", False)

if st.session_state.get("show_history", False):
    st.divider()
    st.markdown("### :material/history: 分析历史")
    history = _load_history()
    if history:
        st.dataframe(
            [{"日期": h["date"], "仓库": h["repo"], "PR": f"#{h['pr_num']}",
              "标题": h["title"][:60], "风险": h["risk_count"], "建议": h["sug_count"],
              "链接": h["url"]}
             for h in history],
            use_container_width=True, hide_index=True,
            column_config={
                "链接": st.column_config.LinkColumn("链接", display_text="打开"),
            },
        )
    else:
        st.caption("暂无历史记录，完成一次分析后自动保存到这里。")
