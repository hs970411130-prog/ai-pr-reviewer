"""Single-file HTML report generator - zero external dependencies."""

from src.models import AnalysisReport
from src.reporter.confidence import confidence_label  # noqa: F401 (kept for compat)


def _is_test_file(filename: str) -> bool:
    parts = filename.lower().replace("\\", "/").split("/")
    return any(p.startswith("test") or p.endswith("_test") for p in parts)


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---- Confidence (1-5) -> CSS level key + badge ----
def _level_key(score: int) -> str:
    return {5: "certain", 4: "high", 3: "medium", 2: "low", 1: "minimal"}.get(
        score, "minimal"
    )


_LEVEL_META = {
    "certain": ("🔴", "确定"),
    "high": ("🟠", "很可能"),
    "medium": ("🟡", "可能"),
    "low": ("🟢", "不太可能"),
    "minimal": ("⚪", "几乎不可能"),
}

_CHEVRON = (
    '<svg class="chevron" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 '
    '4.25a.75.75 0 0 1-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06Z"/></svg>'
)


def _risk_card(r) -> str:
    key = _level_key(r.confidence)
    emoji, label = _LEVEL_META[key]
    sug = (
        f'<div class="f-sug"><b>建议</b> {_esc(r.suggestion)}</div>'
        if getattr(r, "suggestion", "")
        else ""
    )
    return (
        f'<div class="finding lv-{key}" data-level="{key}">'
        '<div class="accent-bar"></div><div class="f-body">'
        f'<div class="f-top"><span class="f-loc">{_esc(r.file)}:{r.line}</span>'
        f'<span class="f-type">{_esc(r.risk_type)}</span>'
        f'<span class="badge">{emoji} {label}</span></div>'
        f'<p class="f-desc">{_esc(r.description)}</p>{sug}</div></div>'
    )


def _sug_card(s) -> str:
    key = _level_key(s.confidence)
    emoji, label = _LEVEL_META[key]
    return (
        f'<div class="finding lv-{key}" data-level="{key}">'
        '<div class="accent-bar"></div><div class="f-body">'
        f'<div class="f-top"><span class="f-loc">{_esc(s.file)}:{s.line}</span>'
        f'<span class="f-type">{_esc(s.category)}</span>'
        f'<span class="badge">{emoji} {label}</span></div>'
        f'<p class="f-desc">{_esc(s.description)}</p></div></div>'
    )


def _section(title: str, cards: str, count: int, sec_id: int) -> str:
    if not cards:
        return ""
    return (
        f'<details class="section" open><summary>{_CHEVRON}{_esc(title)}'
        f'<span class="sec-count" data-sec="{sec_id}">{count}</span></summary>'
        f'<div class="sec-inner" data-sec-body="{sec_id}">{cards}'
        '<div class="empty-note hidden">当前筛选下没有匹配的发现。</div></div></details>'
    )


_CSS = """
<style>
  :root {
    --bg:#fff; --bg-subtle:#f6f8fa; --bg-inset:#f0f2f4;
    --border:#d1d9e0; --border-muted:#e4e8ec;
    --fg:#1f2328; --fg-muted:#59636e; --fg-subtle:#818b96;
    --accent:#0969da; --accent-subtle:#ddf4ff;
    --c-certain:#cf222e; --c-certain-bg:#ffebe9;
    --c-high:#bc4c00;    --c-high-bg:#fff1e5;
    --c-medium:#9a6700;  --c-medium-bg:#fff8c5;
    --c-low:#1a7f37;     --c-low-bg:#dafbe1;
    --c-minimal:#6e7781; --c-minimal-bg:#eaeef2;
    --radius:8px; --shadow:0 1px 0 rgba(31,35,40,.04),0 1px 3px rgba(31,35,40,.06);
  }
  * { box-sizing:border-box; }
  body { font-family:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    background:var(--bg-subtle); color:var(--fg); line-height:1.55; margin:0;
    padding:32px 20px 80px; font-size:14px; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1000px; margin:0 auto; }
  code,.mono { font-family:'IBM Plex Mono',ui-monospace,monospace; }
  .header { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius);
    padding:24px 28px; box-shadow:var(--shadow); margin-bottom:20px; }
  .eyebrow { display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;
    letter-spacing:.04em; text-transform:uppercase; color:var(--fg-subtle); margin-bottom:10px; }
  .eyebrow .dot { width:7px; height:7px; border-radius:50%; background:var(--accent);
    box-shadow:0 0 0 3px var(--accent-subtle); }
  .header h1 { font-size:24px; font-weight:700; margin:0 0 14px; letter-spacing:-.01em; line-height:1.25; }
  .header h1 a { color:var(--fg); text-decoration:none; }
  .header h1 a:hover { color:var(--accent); }
  .meta-row { display:flex; flex-wrap:wrap; gap:8px 18px; color:var(--fg-muted); font-size:13px; }
  .meta-row b { color:var(--fg); font-weight:600; }
  .branch { font-family:'IBM Plex Mono',monospace; font-size:12px; background:var(--bg-inset);
    padding:1px 7px; border-radius:5px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(104px,1fr)); gap:12px; margin-bottom:20px; }
  .stat { background:var(--bg); border:1px solid var(--border-muted); border-radius:var(--radius); padding:14px 16px; }
  .stat .num { font-size:26px; font-weight:700; line-height:1; font-family:'IBM Plex Mono',monospace; }
  .stat .lbl { font-size:12px; color:var(--fg-muted); margin-top:6px; }
  .stat.s-certain .num{color:var(--c-certain);} .stat.s-high .num{color:var(--c-high);}
  .stat.s-medium .num{color:var(--c-medium);} .stat.s-low .num{color:var(--c-low);}
  .stat.s-minimal .num{color:var(--c-minimal);}
  .card { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius);
    box-shadow:var(--shadow); margin-bottom:16px; overflow:hidden; }
  .card-body { padding:18px 22px; }
  .card-body p { margin:0; }
  .pr-desc { border-left:3px solid var(--accent); background:var(--accent-subtle); padding:12px 16px;
    border-radius:6px; white-space:pre-wrap; }
  .pr-desc a { color:var(--accent); }
  details.section { background:var(--bg); border:1px solid var(--border); border-radius:var(--radius);
    box-shadow:var(--shadow); margin-bottom:16px; }
  details.section > summary { list-style:none; cursor:pointer; user-select:none; display:flex;
    align-items:center; gap:10px; padding:16px 22px; font-weight:600; font-size:15px; }
  details.section > summary::-webkit-details-marker { display:none; }
  .chevron { width:16px; height:16px; flex-shrink:0; transition:transform .18s ease; color:var(--fg-muted); }
  details.section[open] > summary .chevron { transform:rotate(90deg); }
  .sec-count { margin-left:auto; font-size:12px; font-weight:500; color:var(--fg-muted);
    background:var(--bg-inset); padding:2px 9px; border-radius:20px; }
  .sec-inner { padding:4px 22px 18px; }
  .finding { display:grid; grid-template-columns:4px 1fr; border:1px solid var(--border-muted);
    border-radius:7px; margin-top:10px; overflow:hidden; transition:box-shadow .15s; }
  .finding:hover { box-shadow:0 2px 8px rgba(31,35,40,.08); }
  .finding .accent-bar { width:4px; }
  .finding .f-body { padding:13px 16px; min-width:0; }
  .f-top { display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:7px; }
  .f-loc { font-family:'IBM Plex Mono',monospace; font-size:12.5px; font-weight:500; color:var(--fg);
    background:var(--bg-inset); padding:2px 8px; border-radius:5px; }
  .f-type { font-size:11.5px; font-weight:600; color:var(--fg-muted); text-transform:uppercase; letter-spacing:.03em; }
  .f-desc { margin:0 0 8px; font-size:13.5px; }
  .f-sug { color:var(--fg-muted); font-size:13px; background:var(--bg-subtle); border-radius:6px;
    padding:8px 11px; border-left:2px solid var(--border); }
  .f-sug b { color:var(--fg); font-weight:600; }
  .badge { display:inline-flex; align-items:center; gap:5px; margin-left:auto; font-size:11.5px;
    font-weight:600; padding:2px 9px; border-radius:20px; white-space:nowrap; }
  .lv-certain .accent-bar{background:var(--c-certain);} .lv-certain .badge{color:var(--c-certain);background:var(--c-certain-bg);}
  .lv-high .accent-bar{background:var(--c-high);} .lv-high .badge{color:var(--c-high);background:var(--c-high-bg);}
  .lv-medium .accent-bar{background:var(--c-medium);} .lv-medium .badge{color:var(--c-medium);background:var(--c-medium-bg);}
  .lv-low .accent-bar{background:var(--c-low);} .lv-low .badge{color:var(--c-low);background:var(--c-low-bg);}
  .lv-minimal .accent-bar{background:var(--c-minimal);} .lv-minimal .badge{color:var(--c-minimal);background:var(--c-minimal-bg);}
  .files-grid { display:grid; gap:1px; background:var(--border-muted); border-radius:7px; overflow:hidden;
    border:1px solid var(--border-muted); }
  .file-row { display:flex; align-items:center; gap:10px; background:var(--bg); padding:8px 14px; font-size:13px; }
  .file-row .fname { font-family:'IBM Plex Mono',monospace; font-size:12.5px; color:var(--fg);
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .file-row .tag { font-size:11px; font-weight:600; color:var(--fg-muted); }
  .file-row .delta { margin-left:auto; font-family:'IBM Plex Mono',monospace; font-size:12px; white-space:nowrap; }
  .delta .add{color:var(--c-low);} .delta .del{color:var(--c-certain);}
  .filterbar { position:sticky; top:12px; z-index:20; background:rgba(255,255,255,.85);
    backdrop-filter:blur(8px); border:1px solid var(--border); border-radius:var(--radius);
    padding:12px 16px; margin-bottom:20px; box-shadow:var(--shadow); display:flex; align-items:center;
    flex-wrap:wrap; gap:10px; }
  .filterbar .fl-label { font-size:12px; font-weight:600; color:var(--fg-muted); }
  .chip { cursor:pointer; user-select:none; border:1px solid var(--border); background:var(--bg);
    font-size:12.5px; font-weight:600; padding:4px 12px; border-radius:20px; color:var(--fg-muted);
    display:inline-flex; align-items:center; gap:6px; transition:all .12s; font-family:inherit; }
  .chip .swatch { width:8px; height:8px; border-radius:50%; }
  .chip[data-on="true"].c-certain{color:var(--c-certain);border-color:var(--c-certain);background:var(--c-certain-bg);}
  .chip[data-on="true"].c-high{color:var(--c-high);border-color:var(--c-high);background:var(--c-high-bg);}
  .chip[data-on="true"].c-medium{color:var(--c-medium);border-color:var(--c-medium);background:var(--c-medium-bg);}
  .chip[data-on="true"].c-low{color:var(--c-low);border-color:var(--c-low);background:var(--c-low-bg);}
  .chip[data-on="true"].c-minimal{color:var(--c-minimal);border-color:var(--c-minimal);background:var(--c-minimal-bg);}
  .chip[data-on="false"] { opacity:.45; }
  .chip.c-certain .swatch{background:var(--c-certain);} .chip.c-high .swatch{background:var(--c-high);}
  .chip.c-medium .swatch{background:var(--c-medium);} .chip.c-low .swatch{background:var(--c-low);}
  .chip.c-minimal .swatch{background:var(--c-minimal);}
  .filterbar .spacer { flex:1; }
  .ghost-btn { cursor:pointer; font-family:inherit; font-size:12.5px; font-weight:500; color:var(--accent);
    background:none; border:none; padding:4px 8px; border-radius:6px; }
  .ghost-btn:hover { background:var(--accent-subtle); }
  .hidden { display:none !important; }
  .empty-note { color:var(--fg-subtle); font-size:13px; padding:14px 4px; font-style:italic; }
  h2.sec-title { font-size:13px; text-transform:uppercase; letter-spacing:.05em; color:var(--fg-subtle);
    font-weight:600; margin:0 0 10px; }
  .skipped { color:var(--fg-subtle); font-size:13px; }
  footer { text-align:center; color:var(--fg-subtle); font-size:12px; margin-top:32px; }
  footer .mono { color:var(--fg-muted); }
</style>
"""

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700'
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
)

_JS = """
<script>
  const active = { certain:true, high:true, medium:true, low:true, minimal:true };
  function applyFilter() {
    document.querySelectorAll('.finding').forEach(el => {
      el.classList.toggle('hidden', !active[el.dataset.level]);
    });
    document.querySelectorAll('[data-sec-body]').forEach(body => {
      const visible = body.querySelectorAll('.finding:not(.hidden)').length;
      const si = body.dataset.secBody;
      const note = body.querySelector('.empty-note');
      if (note) note.classList.toggle('hidden', visible > 0);
      const counter = document.querySelector('[data-sec="' + si + '"]');
      if (counter) counter.textContent = visible;
    });
  }
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const lv = chip.dataset.level;
      active[lv] = !active[lv];
      chip.dataset.on = active[lv];
      applyFilter();
    });
  });
  const expandBtn = document.getElementById('expandAll');
  if (expandBtn) expandBtn.addEventListener('click', (e) => {
    const all = document.querySelectorAll('details.section');
    const anyClosed = [...all].some(d => !d.open);
    all.forEach(d => d.open = anyClosed);
    e.target.textContent = anyClosed ? '全部折叠' : '全部展开';
  });
</script>
"""


def generate(report: AnalysisReport) -> str:
    meta = report.pr_metadata

    # Split source / test
    source_risks = [r for r in report.risks if not _is_test_file(r.file)]
    test_risks = [r for r in report.risks if _is_test_file(r.file)]
    source_sug = [s for s in report.suggestions if not _is_test_file(s.file)]
    test_sug = [s for s in report.suggestions if _is_test_file(s.file)]

    # Stat counts across everything
    counts = {"certain": 0, "high": 0, "medium": 0, "low": 0, "minimal": 0}
    for item in list(report.risks) + list(report.suggestions):
        counts[_level_key(item.confidence)] += 1
    total = sum(counts.values())

    pr_url = f"https://github.com/{meta.owner}/{meta.repo}/pull/{meta.pr_number}"

    # ---- Header ----
    html = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f"<title>PR Review · {_esc(meta.title)}</title>"
        + _FONTS + _CSS + "</head>\n<body>\n<div class=\"wrap\">"
        '<div class="header">'
        f'<span class="eyebrow"><span class="dot"></span>AI PR Review · {total} 项发现</span>'
        f'<h1><a href="{pr_url}" target="_blank">{_esc(meta.title)}</a></h1>'
        '<div class="meta-row">'
        f"<span><b>仓库</b> {_esc(meta.owner)}/{_esc(meta.repo)}</span>"
        f"<span><b>作者</b> {_esc(meta.author)}</span>"
        f'<span><b>分支</b> <span class="branch">{_esc(meta.head_branch)} → {_esc(meta.base_branch)}</span></span>'
        f"<span><b>变更文件</b> {len(report.file_changes)}</span>"
        "</div></div>"
    )

    # ---- Stat bar ----
    stat_defs = [
        ("certain", "确定"), ("high", "很可能"), ("medium", "可能"),
        ("low", "不太可能"), ("minimal", "几乎不可能"),
    ]
    stats = '<div class="stats">'
    for key, lbl in stat_defs:
        if counts[key] == 0 and key == "minimal":
            continue  # hide the rarely-used lowest tier when empty
        stats += (
            f'<div class="stat s-{key}"><div class="num">{counts[key]}</div>'
            f'<div class="lbl">{lbl}</div></div>'
        )
    stats += f'<div class="stat"><div class="num">{total}</div><div class="lbl">总发现</div></div></div>'
    html += stats

    # ---- Summary ----
    if report.summary:
        html += (
            '<div class="card"><div class="card-body">'
            '<h2 class="sec-title">摘要</h2>'
            f"<p>{_esc(report.summary)}</p></div></div>"
        )

    # ---- Description + Context ----
    if meta.body or (report.context and report.context.analysis_text):
        inner = ""
        if meta.body:
            inner += f'<div class="pr-desc">{_esc(meta.body)}</div>'
        if report.context and report.context.analysis_text:
            inner += (
                f'<p style="margin-top:14px;color:var(--fg-muted);">'
                f"{_esc(report.context.analysis_text)}</p>"
            )
        html += (
            f'<details class="section" open><summary>{_CHEVRON}背景与描述</summary>'
            f'<div class="sec-inner">{inner}</div></details>'
        )

    # ---- Filter bar ----
    chips = ""
    for key, lbl in stat_defs:
        if counts[key] == 0 and key == "minimal":
            continue
        chips += (
            f'<button class="chip c-{key}" data-level="{key}" data-on="true">'
            f'<span class="swatch"></span>{lbl}</button>'
        )
    html += (
        '<div class="filterbar"><span class="fl-label">按置信度筛选</span>'
        + chips
        + '<span class="spacer"></span>'
        '<button class="ghost-btn" id="expandAll">全部折叠</button></div>'
    )

    # ---- Finding sections ----
    html += _section(
        "风险发现",
        "".join(_risk_card(r) for r in source_risks),
        len(source_risks), 0,
    )
    html += _section(
        "测试代码风险",
        "".join(_risk_card(r) for r in test_risks),
        len(test_risks), 1,
    )
    html += _section(
        "Review 建议",
        "".join(_sug_card(s) for s in source_sug),
        len(source_sug), 2,
    )
    html += _section(
        "测试代码建议",
        "".join(_sug_card(s) for s in test_sug),
        len(test_sug), 3,
    )

    # ---- Changed files ----
    if report.file_changes:
        rows = ""
        for fc in report.file_changes:
            symbol = {"added": "+", "modified": "M", "removed": "-", "renamed": "R"}.get(
                fc.change_type.value, "?"
            )
            rows += (
                '<div class="file-row">'
                f'<span class="tag">[{symbol}]</span>'
                f'<span class="fname">{_esc(fc.filename)}</span>'
                f'<span class="delta"><span class="add">+{fc.additions}</span> '
                f'<span class="del">-{fc.deletions}</span></span></div>'
            )
        html += (
            f'<details class="section"><summary>{_CHEVRON}变更文件'
            f'<span class="sec-count">{len(report.file_changes)}</span></summary>'
            f'<div class="sec-inner"><div class="files-grid">{rows}</div></div></details>'
        )

    # ---- Skipped files ----
    if report.skipped_files:
        items = "".join(f"<li>{_esc(f)}</li>" for f in report.skipped_files)
        html += (
            f'<details class="section"><summary>{_CHEVRON}跳过的文件（过大）'
            f'<span class="sec-count">{len(report.skipped_files)}</span></summary>'
            f'<div class="sec-inner"><ul class="skipped">{items}</ul></div></details>'
        )

    html += (
        '<footer>由 <span class="mono">ai-pr-review</span> 生成 · DeepSeek-V4</footer>'
        "</div>" + _JS + "</body></html>"
    )
    return html
