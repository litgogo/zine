#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""康奈尔笔记电子杂志生成器 —— 复刻「自习室 STUDY ROOM · Cornell Notes Series」版式

版式结构（每页 A4 竖版）：
  顶部栏目带： 选择 | 行动 | 坚持 | 收获
  左栏（窄）： 关键词 / 线索（cue column）
  右栏（宽）： 笔记正文（对话实录，说话人加粗）
  可选金句框： 居中大字块
  底部总结带： 总结 + 2-4 行摘要
  右下角页码： N/19

用法：由 build(ep) 生成 zines/<slug>.html
"""
import os
import html as _h
import importlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 输出目录：CLI --out 覆盖；作为库调用时，默认写到当前目录
OUT = os.path.expanduser('~/.hermes/workspace/zine-site/zines')

COLS = ["选择", "行动", "坚持", "收获"]

# 配色档：quiet = CornellCast 低饱和（默认，Gogo 2026-10 定的规范）；classic = 早期白底细灰稿
PALETTES = {
    "quiet": {
        "paper": "#F8F7F3", "ink": "#353A37", "ink2": "#626763", "ink3": "#8A8F8B",
        "rule": "#DCDCD5", "rule2": "#E7E6E0", "tint": "#F1F0EA", "accent": "#6C6A62",
        "c1": "#DCD4E7", "c2": "#E8D7DB", "c3": "#EDE5C8", "c4": "#DCE7EA", "c5": "#DCE5DA",
        "spk_a": "#5B4A78", "spk_b": "#37573F", "spk_c": "#6E5A2E",
    },
    "classic": {
        "paper": "#ffffff", "ink": "#1c1c1c", "ink2": "#55544f", "ink3": "#8d8b84",
        "rule": "#cfcdc5", "rule2": "#e6e4dd", "tint": "#f4f3ef", "accent": "#6b5842",
        "c1": "transparent", "c2": "transparent", "c3": "transparent", "c4": "transparent",
        "c5": "transparent", "spk_a": "#6b5842", "spk_b": "#6b5842", "spk_c": "#6b5842",
    },
}


def root_css(name):
    p = PALETTES.get(name) or PALETTES["quiet"]
    return (":root {\n"
            f"  --ink: {p['ink']};\n  --ink-2: {p['ink2']};\n  --ink-3: {p['ink3']};\n"
            f"  --rule: {p['rule']};\n  --rule-2: {p['rule2']};\n  --paper: {p['paper']};\n"
            f"  --tint: {p['tint']};\n  --accent: {p['accent']};\n"
            f"  --c1: {p['c1']};\n  --c2: {p['c2']};\n  --c3: {p['c3']};\n"
            f"  --c4: {p['c4']};\n  --c5: {p['c5']};\n"
            f"  --spk-a: {p['spk_a']};\n  --spk-b: {p['spk_b']};\n  --spk-c: {p['spk_c']};\n"
            "}")


def esc(s):
    return _h.escape(s, quote=False)


def cues_html(items, tones=None):
    """线索栏。每条可以是 "标题\n提示" 的字符串，或 {"q":..., "hint":..., "tone":1..3} 的字典。"""
    out = ""
    for i, it in enumerate(items):
        if isinstance(it, dict):
            head = it.get("q") or it.get("title") or ""
            hint = it.get("hint") or ""
            tone = it.get("tone") or (i % 3 + 1)
        else:
            lines = str(it).split("\n")
            head, hint = lines[0], "\n".join(lines[1:])
            tone = i % 3 + 1
        cls = f"cue c{tone}" if tone in (1, 2, 3) else "cue"
        out += f'<div class="{cls}">'
        out += f'<div class="cue-h">{esc(head)}</div>'
        if hint:
            out += '<div class="cue-b">' + "<br>".join(esc(x) for x in hint.split("\n")) + "</div>"
        out += "</div>"
    return out


_SPK_ORDER = {}


def _spk_cls(name):
    """说话人 → 稳定色档（同一份稿里同一个人始终同色，最多三档）。"""
    if name not in _SPK_ORDER:
        _SPK_ORDER[name] = 'abc'[len(_SPK_ORDER) % 3]
    return "who w-" + _SPK_ORDER[name]


def body_html(paras):
    """正文段落：("说话人", "文字") 元组，或 {"speaker":.., "ts":.., "text":..} 字典。"""
    out = ""
    for p in paras:
        if isinstance(p, dict) and p.get("divider"):
            out += f'<div class="ch-div">{esc(p["divider"])}</div>'
            continue
        if isinstance(p, dict):
            who, txt = p.get("speaker") or "", p.get("text") or ""
            tag = p.get("tag") or ""
            ts = p.get("ts") or ""
            head = (f'<span class="tag">{esc(tag)}</span>' if tag else "")
            head += (f'<span class="{_spk_cls(who)}">{esc(who)}</span>' if who else "")
            tail = f'<span class="its">{esc(ts)}</span>' if ts else ""
            out += f'<p class="dlg">{head}{esc(txt)}{tail}</p>'
        elif isinstance(p, tuple):
            who, txt = p
            out += f'<p class="dlg"><span class="{_spk_cls(who)}">{esc(who)}</span>{esc(txt)}</p>'
        else:
            out += f'<p class="dlg">{esc(p)}</p>'
    return out


def _body_len(it):
    if isinstance(it, dict) and it.get("divider"):
        return 0
    return len(it["text"]) if isinstance(it, dict) else len(it[1])


def _body_ts(it):
    if isinstance(it, dict) and it.get("divider"):
        return ""
    return (it.get("ts") or "") if isinstance(it, dict) else ""


def chunk_body(items, limit=1050, max_items=6):
    """把正文按字数与条目数拆块（不拆散单段）。条目上限是为了给左侧线索栏与页底留出空间。"""
    chunks, cur, n = [], [], 0
    for it in items:
        ln = _body_len(it)
        if cur and (n + ln > limit or len(cur) >= max_items):
            chunks.append(cur)
            cur, n = [], 0
        cur.append(it)
        n += ln
    if cur:
        chunks.append(cur)
    return chunks


def band_html(ep):
    cols = ep.get("band") or COLS
    return "".join(f'<div class="band-c">{esc(c)}</div>' for c in cols)


def page_html(pg, idx, total, chunk=None, nchunks=1, ts_label=None):
    """chunk=None 表示整页；否则 chunk 是本页正文的一段（续页）。"""
    body = pg["body"] if chunk is None else chunk
    first, last = (chunk is None or pg.get("_chunk_i", 0) == 0), (chunk is None or pg.get("_chunk_i", 0) == nchunks - 1)
    parts = ['<section class="page">']
    _markline = f'<div class="marklink">{esc(pg["mark_link"])}</div>' if pg.get("mark_link") else "" 
    parts.append('<header class="band">' + "".join(
        f'<div class="band-c">{c}</div>' for c in ((pg.get("_band") or COLS))) + "</header>")
    title = esc(pg["title"]) + ("" if first else ' <span class="cont">（续）</span>')
    ts = esc(ts_label or pg.get("ts_range", ""))
    parts.append(f'<div class="p-title">{title}<span class="p-ts">{ts}</span></div>')
    if _markline:
        parts.append(_markline)
    parts.append('<div class="grid">')
    cues = pg.get("_cues") or pg["cues"]
    kws = pg.get("_kws") or []
    kw_html = ('<div class="kw-wrap">' + "".join(f'<span class="kw">{esc(k)}</span>' for k in kws) + "</div>") if kws else ""
    parts.append('<aside class="col-cue">'
                 + (cues_html(cues) if cues else '<div class="cue cue-cont"></div>')
                 + kw_html
                 + (f'<div class="cue-foot">本章小结见 p.{pg["_sum_pno"]}</div>'
                    if (not last and pg.get("_sum_pno")) else "")
                 + "</aside>")
    parts.append('<div class="col-note">' + body_html(body) + "</div>")
    parts.append("</div>")
    if last and pg.get("callout"):
        parts.append('<div class="callout">' + esc(pg["callout"]).replace("\n", "<br>") + "</div>")
    if last and pg.get("summary"):
        parts.append('<footer class="sum">')
        parts.append(f'<div class="sum-label">{esc(LABELS["summary"])}</div>')
        parts.append('<div class="sum-text">' + esc(pg["summary"])
                     + (f'<div class="recall">{esc(pg["recall"])}</div>' if pg.get("recall") else "")
                     + "</div>")
        parts.append("</footer>")
    if pg.get("_personal", True):
        q = pg.get("_refq") or "这段内容与我有什么关系？"
        lines = pg.get("my_thoughts") or ""
        body = f'<div class="ref-text">{esc(lines)}</div>' if lines else \
               '<div class="ref-lines">' + "".join('<div class="ref-line"></div>' for _ in range(1)) + "</div>"
        parts.append('<footer class="ref">'
                     '<div class="ref-label">PERSONAL REFLECTION<b>我的思考</b></div>'
                     f'<div class="ref-body"><div class="ref-q">{esc(q)}</div>{body}</div>'
                     "</footer>")
    parts.append(f'<div class="pno">{idx}/{total}</div>')
    parts.append("</section>")
    return "\n".join(parts)


CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
/*__ROOT__*/
html { background: #dedcd6; }
body {
  font-family: "Noto Sans SC", -apple-system, sans-serif;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  padding: 28px 0;
}
.page {
  position: relative;
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto 22px;
  padding: 14mm 15mm 16mm;
  background: var(--paper);
  box-shadow: 0 3px 18px rgba(0,0,0,.16);
  display: flex;
  flex-direction: column;
}
/* ---------- 顶部栏目带 ---------- */
.band {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  border-bottom: 1.6px solid var(--rule);
  padding-bottom: 3px;
  margin-bottom: 9mm;
}
.band-c {
  font-size: 10.5px;
  letter-spacing: .28em;
  color: var(--ink-3);
  font-weight: 500;
}
.p-title {
  font-family: "Noto Serif SC", serif;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: .04em;
  margin-bottom: 6mm;
  color: var(--ink);
}
/* ---------- 双栏 ---------- */
.grid { display: grid; grid-template-columns: 27% 73%; column-gap: 7mm; flex: 1; }
.col-cue { border-right: 1px solid var(--rule-2); padding-right: 5mm; }
.cue { margin-bottom: 4mm; padding: 2.6mm 3.2mm; border-radius: 3px; background: transparent; }
.cue.c1 { background: var(--c1); }
.cue.c2 { background: var(--c2); }
.cue.c3 { background: var(--c3); }
.cont { font-size: 11px; font-weight: 400; color: var(--ink-3); letter-spacing: .1em; }
.p-ts { font-family: "Noto Sans Mono", monospace; font-size: 9.5px; color: var(--ink-3); letter-spacing: .14em; font-weight: 400; margin-left: 4mm; }
.cue-cont { min-height: 1px; }
.kw-wrap { display: flex; flex-wrap: wrap; gap: 1.6mm; margin-top: 4.5mm; }
.kw { font-size: 9.5px; line-height: 1.4; padding: 1.1mm 2.4mm; border: 1px solid var(--rule);
      border-radius: 999px; color: var(--ink-2); letter-spacing: .02em; }
.cue-foot { margin-top: 4mm; padding-top: 2.5mm; border-top: 1px dashed var(--rule); font-size: 9.5px; color: var(--ink-3); letter-spacing: .06em; }
.tag { font-size: 9px; letter-spacing: .1em; color: var(--ink-3); border: 1px solid var(--rule);
       border-radius: 2px; padding: 0.3mm 1.4mm; margin-right: 2mm; vertical-align: .8px; }
.its { font-family: "Noto Sans Mono", monospace; font-size: 9px; color: var(--ink-3); margin-left: 1.6mm; letter-spacing: .04em; }
.recall { font-size: 10px; color: var(--ink-3); margin-top: 2.2mm; letter-spacing: .04em; }
.cue-h { font-size: 12px; font-weight: 700; color: var(--ink); line-height: 1.5; letter-spacing: .02em; }
.cue-b { font-size: 10.5px; color: var(--ink-2); line-height: 1.72; margin-top: 2px; }
.col-note { }
.dlg { font-size: 12.2px; line-height: 1.86; color: #2c2b28; margin-bottom: 2.5mm; text-align: justify; }
.who { font-weight: 700; color: var(--accent); margin-right: .5em; letter-spacing: .02em; }
.who.w-a { color: var(--spk-a); }
.who.w-b { color: var(--spk-b); }
.who.w-c { color: var(--spk-c); }
/* ---------- 金句框 ---------- */
.callout {
  margin: 7mm 0 6mm;
  padding: 6mm 8mm;
  background: var(--tint);
  border-left: 2.5px solid var(--accent);
  font-family: "Noto Serif SC", serif;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.75;
  letter-spacing: .06em;
  color: var(--ink);
  text-align: center;
}
/* ---------- 总结带 ---------- */
.sum {
  margin-top: auto;
  border-top: 1.6px solid var(--rule);
  padding-top: 3.5mm;
  display: grid;
  grid-template-columns: 26% 74%;
  column-gap: 8mm;
}
.sum-label { font-size: 11px; font-weight: 700; letter-spacing: .18em; color: var(--ink-3); }
.sum-text { font-size: 10.8px; line-height: 1.7; color: var(--ink-2); }
/* ---------- 页码 ---------- */
.pno {
  position: absolute;
  right: 15mm;
  bottom: 7mm;
  font-family: "Noto Sans Mono", monospace;
  font-size: 9.5px;
  color: var(--ink-3);
}
/* ---------- 封面 ---------- */
.cover { justify-content: space-between; padding: 22mm 18mm 16mm; }
.cover-top { text-align: center; }
.cover-brand {
  font-family: "Noto Sans Mono", monospace;
  font-size: 11px;
  letter-spacing: .42em;
  color: var(--ink-3);
  text-transform: uppercase;
}
.cover-mark {
  display: inline-block;
  margin-top: 6mm;
  padding: 4px 16px;
  border: 1px solid var(--rule);
  font-size: 10px;
  letter-spacing: .3em;
  color: var(--ink-3);
}
.cover-mid { text-align: center; margin: 0; }
.cover-num {
  font-family: "Noto Sans Mono", monospace;
  font-size: 13px;
  letter-spacing: .4em;
  color: var(--ink-3);
  margin-bottom: 4mm;
}
.cover-title {
  font-family: "Noto Serif SC", serif;
  font-size: 62px;
  font-weight: 900;
  letter-spacing: .16em;
  line-height: 1.15;
  color: var(--ink);
}
.cover-en {
  font-family: "Noto Sans Mono", monospace;
  font-size: 11px;
  letter-spacing: .52em;
  color: var(--ink-3);
  margin-top: 5mm;
}
.cover-sub {
  font-family: "Noto Serif SC", serif;
  font-size: 19px;
  letter-spacing: .22em;
  color: var(--ink-2);
  margin-top: 11mm;
}
.cover-line {
  font-size: 12.5px;
  letter-spacing: .18em;
  color: var(--ink-3);
  margin-top: 6mm;
}
.cover-rule { width: 44px; height: 1.5px; background: var(--accent); margin: 9mm auto 0; }
.cover-bottom { text-align: center; }
.cover-foot {
  font-family: "Noto Sans Mono", monospace;
  font-size: 10px;
  letter-spacing: .28em;
  color: var(--ink-3);
  line-height: 2.1;
}
/* ---------- 导航页 ---------- */
.nav-h {
  font-family: "Noto Serif SC", serif;
  font-size: 17px;
  letter-spacing: .2em;
  font-weight: 700;
  margin-bottom: 9mm;
}
.nav-i {
  display: grid;
  grid-template-columns: 12mm 1fr;
  font-size: 13px;
  color: var(--ink-2);
  line-height: 2.5;
  border-bottom: 1px solid var(--rule-2);
  padding: 1.6mm 0;
}
.nav-n { font-family: "Noto Sans Mono", monospace; color: var(--ink-3); font-size: 11px; }
/* ---------- 金句回顾页 ---------- */
.quote-list { margin-top: 2mm; }
.lead { font-size: 11px; line-height: 1.9; color: var(--ink-3); margin: -4mm 0 6mm; letter-spacing: .04em; }
.quote-list.big .quote-row { font-size: 15.5px; padding: 5mm 0 5mm 9mm; }
.quote-list.big .quote-row::before { top: 5mm; font-size: 11px; }
.quote-list.big .quote-row:nth-child(2n) { background: var(--tint); }
.quote-row {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  line-height: 1.9;
  color: var(--ink);
  padding: 3.6mm 0 3.6mm 8mm;
  position: relative;
  border-bottom: 1px solid var(--rule-2);
}
.quote-row::before {
  content: "◆";
  position: absolute;
  left: 0;
  top: 3.6mm;
  color: var(--accent);
  font-size: 10px;
}
/* ---------- 我的思考 ---------- */
.ref {
  margin-top: 5mm; border-top: 1px solid var(--rule); padding-top: 3.5mm;
  display: grid; grid-template-columns: 26% 74%; column-gap: 8mm;
}
.ref-label { font-family: "Noto Sans Mono", monospace; font-size: 9px; letter-spacing: .16em; color: var(--ink-3); line-height: 1.6; }
.ref-label b { display: block; font-family: "Noto Sans SC", sans-serif; font-size: 11px; letter-spacing: .1em; color: var(--ink-2); margin-top: 1.5mm; }
.ref-body { }
.ref-q { font-size: 11.5px; color: var(--ink-2); letter-spacing: .04em; }
.ref-lines { margin-top: 2.6mm; }
.ref-line { border-bottom: 1px dotted var(--rule); height: 6.6mm; }
.ref-text { font-size: 11.5px; line-height: 1.85; color: var(--ink); margin-top: 1.6mm; }

/* ---------- 全期回顾页 ---------- */
.rv-h { font-size: 11px; font-weight: 700; letter-spacing: .18em; color: var(--ink-3); margin: 6mm 0 3mm; }
.rv-list { display: flex; flex-direction: column; }
.rv-i, .rv-q {
  display: grid; grid-template-columns: 11mm 1fr; column-gap: 3mm;
  padding: 3.4mm 0; border-bottom: 1px solid var(--rule-2);
  font-size: 12.4px; line-height: 1.9; color: #2c2b28; text-align: justify;
}
.rv-i:nth-child(odd) { background: var(--tint); }
.rv-q { font-size: 12.2px; }
.rv-n { font-family: "Noto Sans Mono", monospace; font-size: 10px; color: var(--ink-3); letter-spacing: .08em; padding-top: 1mm; }

/* ---------- 尾页 ---------- */
.end-page { justify-content: center; text-align: center; }
.end-big {
  font-family: "Noto Serif SC", serif;
  font-size: 22px;
  font-weight: 700;
  line-height: 2;
  letter-spacing: .04em;
  color: var(--ink);
}
.end-small { font-size: 13px; color: var(--ink-2); margin-top: 8mm; letter-spacing: .12em; }
.end-rule { width: 60px; height: 1.5px; background: var(--accent); margin: 12mm auto; }
.end-meta {
  font-family: "Noto Sans Mono", monospace;
  font-size: 10px;
  letter-spacing: .26em;
  color: var(--ink-3);
  line-height: 2.2;
}
.back-home {
  display: inline-block;
  margin-top: 10mm;
  font-size: 11px;
  letter-spacing: .16em;
  color: var(--ink-3);
  text-decoration: none;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 2px;
}
.back-home:hover { color: var(--accent); }

@media print {
  html { background: #fff; }
  body { padding: 0; }
  .page { box-shadow: none; margin: 0; page-break-after: always; }
  .page:last-child { page-break-after: auto; }
  @page { size: A4; margin: 0; }
}
"""


CSS_CHAIN = """
.chain-list { display: flex; flex-direction: column; gap: 4.5mm; margin-top: 2mm; }
.chain-i { border-left: 2px solid var(--accent); padding-left: 4mm; }
.chain-h { display: flex; align-items: baseline; gap: 3mm; margin-bottom: 1mm; }
.chain-n { font-family: "Noto Sans Mono", monospace; font-size: 11px; color: var(--accent); letter-spacing: .1em; }
.chain-ts { font-family: "Noto Sans Mono", monospace; font-size: 10px; color: var(--ink-3); }
.chain-spk { font-size: 10px; color: var(--ink-3); letter-spacing: .08em; }
.chain-t { font-size: 12.5px; line-height: 1.72; color: var(--ink); }
.chain-l { font-size: 11px; line-height: 1.7; color: var(--ink-2); margin-top: 1.2mm; }
.chain-l::before { content: "↳ "; color: var(--accent); }
.ch-div { font-size: 11px; font-weight: 700; color: var(--ink); letter-spacing: .08em;
          margin: 3.4mm 0 2mm; padding-top: 2mm; border-top: 1px solid var(--rule); }
.marklink { margin: 0 0 3mm; padding: 2.2mm 3mm; background: var(--tint-a); border-left: 2px solid var(--accent);
            font-size: 10.5px; line-height: 1.6; color: var(--ink-2); letter-spacing: .03em; }
"""

LABELS = {"summary": "本页小结"}
PERSONAL = {"on": True, "q": "这段内容与我有什么关系？"}


def build(ep, palette=None):
    global LABELS, COLS
    LABELS = dict(LABELS, **(ep.get("labels") or {}))
    if ep.get("band"):
        COLS = list(ep["band"])
    PERSONAL["on"] = bool(ep.get("personal_reflection", True))
    PERSONAL["q"] = ep.get("reflection_question") or PERSONAL["q"]
    pal = palette or ep.get("palette") or "quiet"
    slug = ep["slug"]
    pages = ""
    _ttitle = "<br>".join(esc(x) for x in str(ep["title"]).split("\n"))
    _tlen = max(len(x) for x in str(ep["title"]).split("\n"))
    _tsize = 62 if _tlen <= 6 else (54 if _tlen <= 8 else 46)

    # 封面
    pages += f"""<section class="page cover">
  <div class="cover-top">
    <div class="cover-brand">{esc(ep.get('cover_brand', 'Study Room'))}</div>
    <div class="cover-mark">{esc(ep.get('cover_mark', 'Cornell Notes Series'))}</div>
  </div>
  <div class="cover-mid">
    <div class="cover-num">{esc(ep['num'])} | {esc(ep['num_en'])}</div>
    <div class="cover-title" style="font-size:{_tsize}px">{_ttitle}</div>
    <div class="cover-en">{esc(ep['title_en'])}</div>
    <div class="cover-sub">{esc(ep['subtitle'])}</div>
    <div class="cover-line">{esc(ep['tagline'])}</div>
    <div class="cover-rule"></div>
  </div>
  <div class="cover-bottom">
    <div class="cover-foot">{esc(ep['show'])}<br>{esc(ep['date_label'])}</div>
  </div>
</section>"""

    # 导航
    nav = "".join(
        f'<div class="nav-i"><span class="nav-n">{esc(n)}</span><span>{esc(t)}</span></div>'
        for n, t in ep["nav"])
    pages += f"""<section class="page">
  <header class="band"><div class="band-c">本期导航</div><div class="band-c"></div><div class="band-c"></div><div class="band-c"></div></header>
  <div class="nav-h">本期导航</div>
  {nav}
</section>"""

    # 她的标记链：把用户的高亮串成一条线
    if ep.get("chain"):
        ch = ep["chain"]
        rows = ""
        for i, it in enumerate(ch["items"], 1):
            rows += (f'<div class="chain-i">'
                     f'<div class="chain-h"><span class="chain-n">{i:02d}</span>'
                     f'<span class="chain-ts">{esc(it.get("ts", ""))}</span>'
                     f'<span class="chain-spk">{esc(it.get("spk", ""))}</span></div>'
                     f'<div class="chain-t">{esc(it.get("text", ""))}</div>'
                     + (f'<div class="chain-l">{esc(it["link"])}</div>' if it.get("link") else "")
                     + '</div>')
        chain_page_html = f"""<section class="page">
  <header class="band">{band_html(ep)}</header>
  <div class="nav-h">{esc(ch.get("title", "她的标记链"))}</div>
  <div class="lead">{esc(ch.get("lead", ""))}</div>
  <div class="chain-list">{rows}</div>
  <div class="pno">{{PNO}}</div>
</section>"""

    limit = int(ep.get("chars_per_page", 1050))
    max_items = int(ep.get("items_per_page", 6))
    plan = []
    for pg in ep["pages"]:
        chunks = chunk_body(pg["body"], limit, max_items)
        cues = pg.get("cues") or []
        kws = pg.get("keywords") or []
        k = len(chunks)
        q, r = (len(cues) // k, len(cues) % k) if k else (0, 0)
        cut, slices = 0, []
        for ci in range(k):
            take = q + (1 if ci < r else 0)
            slices.append(cues[cut:cut + take] if take else [])
            cut += take
        q2, r2 = (len(kws) // k, len(kws) % k) if k else (0, 0)
        cut2, kslice = 0, []
        for ci in range(k):
            take = q2 + (1 if ci < r2 else 0)
            kslice.append(kws[cut2:cut2 + take] if take else [])
            cut2 += take
        for ci, ch in enumerate(chunks):
            plan.append((pg, ch, ci, k, slices[ci], kslice[ci]))
    n_chain = 1 if ep.get("chain") else 0
    n_res = 0
    if ep.get("resonance"):
        n_res = len(ep["resonance"]) if isinstance(ep["resonance"], list) else 1
    n_q = 1 if ep.get("quotes") else 0
    n_rev = (2 if (ep.get("review") or {}).get("questions") else 1) if ep.get("review") else 0
    total = 2 + n_chain + len(plan) + n_res + n_q + n_rev + 1
    if ep.get("chain"):
        pages += chain_page_html.replace("{PNO}", f"3/{total}")   # 封面+导航+正文页+共振页+金句页+回顾页+尾页
    pno = 3 + n_chain
    first_pno = {}
    for pg, ch, ci, cn, cu, kw in plan:
        base = id(pg)
        first_pno.setdefault(base, pno)
        sum_pno = first_pno[base] + cn - 1
        pg = dict(pg, _chunk_i=ci, _cues=cu, _kws=kw, _sum_pno=sum_pno,
                  _personal=(PERSONAL["on"] and ci == cn - 1), _refq=PERSONAL["q"])
        ts = (f'{_body_ts(ch[0])}–{_body_ts(ch[-1])}' if ch and _body_ts(ch[0]) else pg.get("ts_range", ""))
        pages += page_html(pg, pno, total, chunk=ch, nchunks=cn, ts_label=ts)
        pno += 1
    pno += n_res
    quotes_pno = pno
    review_pno = pno + n_q

    # 我的共振（可选：Gogo 的原话层，原样收录；支持单个 dict 或 dict 列表分段）
    if ep.get("resonance"):
        blocks = ep["resonance"] if isinstance(ep["resonance"], list) else [ep["resonance"]]
        for res in blocks:
            label = res.get("label", "我的共振")
            rrows = "".join(f'<div class="quote-row">{esc(q)}</div>' for q in res["lines"])
            foot = f"""  <footer class="sum">
    <div class="sum-label">落款</div>
    <div class="sum-text">{esc(res.get('foot', ''))}</div>
  </footer>
""" if res.get("foot") else ""
            pages += f"""<section class="page">
  <header class="band"><div class="band-c">{esc(label)}</div><div class="band-c"></div><div class="band-c"></div><div class="band-c"></div></header>
  <div class="nav-h">{esc(label)}</div>
  <div class="quote-list">{rrows}</div>
{foot}</section>"""

    # 金句回顾（有 quotes 才出）
    if ep.get("quotes"):
        qs = "".join(f'<div class="quote-row">{esc(q)}</div>' for q in ep["quotes"])
        pages += f"""<section class="page">
  <header class="band">{band_html(ep)}</header>
  <div class="nav-h">本期金句回顾</div>
  <div class="lead">{esc(ep.get("quotes_lead", "以下为节目原话，括号内是该句在录音里的位置；逐字稿未逐句听校，引用前请对回音频。"))}</div>
  <div class="quote-list big">{qs}</div>
  <div class="pno">{quotes_pno}/{total}</div>
</section>"""

    # 全期回顾：关键观点 + 主动回忆题
    if ep.get("review"):
        rv = ep["review"]
        pts = "".join(f'<div class="rv-i"><span class="rv-n">{i:02d}</span><span>{esc(p)}</span></div>'
                      for i, p in enumerate(rv["points"], 1))
        qs2 = "".join(f'<div class="rv-q"><span class="rv-n">Q{i}</span><span>{esc(q)}</span></div>'
                      for i, q in enumerate(rv.get("questions", []), 1))
        pages += f"""<section class="page">
  <header class="band">{band_html(ep)}</header>
  <div class="nav-h">{esc(rv.get("title", "全期回顾"))}</div>
  <div class="lead">{esc(rv.get("lead", ""))}</div>
  <div class="rv-h">关键观点（括号内是这句在录音里的位置）</div>
  <div class="rv-list">{pts}</div>
  <div class="pno">{review_pno}/{total}</div>
</section>"""
        if rv.get("questions"):
            pages += f"""<section class="page">
  <header class="band">{band_html(ep)}</header>
  <div class="nav-h">主动回忆</div>
  <div class="lead">先不看前面，自己答一遍；答不出来再翻回对应章节。</div>
  <div class="rv-list">{qs2}</div>
  <div class="pno">{review_pno + 1}/{total}</div>
</section>"""

    # 尾页
    pages += f"""<section class="page end-page">
  <div class="end-big">{'<br>'.join(esc(x) for x in ep['end_lines'])}</div>
  <div class="end-small">{esc(ep['tagline'])}</div>
  <div class="end-rule"></div>
  <div class="end-meta">
    {esc(ep.get('end_meta', '自习室学习委员课堂笔记'))}<br>
    {esc(ep.get('end_title', ep['title']))} × {esc(ep.get('end_subtitle', ep['subtitle']))}<br>
    {esc(ep.get('end_note', '进步是最性感的事'))}
  </div>
  <a class="back-home" href="../index.html">{esc(ep.get('back_label', '← 返回档案首页'))}</a>
</section>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cornell Notes · {esc(ep['title'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@300;400;500;700&family=Noto+Sans+Mono&display=swap" rel="stylesheet">
<style>{CSS.replace("/*__ROOT__*/", root_css(pal))}{CSS_CHAIN}</style>
</head>
<body>
{pages}
</body>
</html>
"""
    path = os.path.join(OUT, f"{slug}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def load_data(path):
    """从 .py 数据文件里取 EP 字典（文件里写 EP = {...}）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ep_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EP


def main():
    import argparse
    ap = argparse.ArgumentParser(description="康奈尔笔记电子杂志生成器")
    ap.add_argument("data", nargs="?", help="数据文件（.py，内含 EP = {...}）")
    ap.add_argument("--out", default=".", help="输出目录（默认当前目录，生成 <slug>.html）")
    ap.add_argument("--pdf", action="store_true", help="同时用 Chrome 打印为 A4 PDF")
    ap.add_argument("--chrome", default="google-chrome")
    ap.add_argument("--palette", choices=list(PALETTES), default="quiet",
                    help="配色档：quiet=低饱和（默认，CornellCast 规范）；classic=早期白底细灰")
    a = ap.parse_args()
    if not a.data:
        ap.error("需要数据文件：python3 gen_cornell.py templates/episode-data.example.py --out examples")
    global OUT
    OUT = os.path.abspath(a.out)
    os.makedirs(OUT, exist_ok=True)
    ep = load_data(a.data)
    path = build(ep, palette=a.palette)
    print("wrote", path)
    if a.pdf:
        import subprocess
        pdf = os.path.splitext(path)[0] + ".pdf"
        subprocess.run([a.chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", "file://" + path], check=False)
        print("pdf", pdf)


def build_all():
    """站点模式：遍历 episodes_data.EPISODES 里 style==cornell 的期，逐个写入 zines/。"""
    from episodes_data import EPISODES
    import importlib
    n = 0
    for e in EPISODES:
        if e.get("style") != "cornell":
            continue
        mod = importlib.import_module(e["cornell_data"])
        print("wrote", build(mod.EP), "[康奈尔笔记风格]")
        n += 1
    print(f"共 {n} 期使用康奈尔笔记风格")


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1:
        main()
    else:
        build_all()
