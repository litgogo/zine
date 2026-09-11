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

OUT = os.path.expanduser('~/.hermes/workspace/zine-site/zines')
os.makedirs(OUT, exist_ok=True)

COLS = ["选择", "行动", "坚持", "收获"]


def esc(s):
    return _h.escape(s, quote=False)


def cues_html(items):
    out = ""
    for it in items:
        lines = it.split("\n")
        out += '<div class="cue">'
        out += f'<div class="cue-h">{esc(lines[0])}</div>'
        if len(lines) > 1:
            out += '<div class="cue-b">' + "<br>".join(esc(x) for x in lines[1:]) + "</div>"
        out += "</div>"
    return out


def body_html(paras):
    out = ""
    for p in paras:
        if isinstance(p, tuple):
            who, txt = p
            out += f'<p class="dlg"><span class="who">{esc(who)}</span>{esc(txt)}</p>'
        else:
            out += f'<p class="dlg">{esc(p)}</p>'
    return out


def page_html(pg, idx, total):
    parts = ['<section class="page">']
    # 顶部栏目带
    parts.append('<header class="band">' + "".join(
        f'<div class="band-c">{c}</div>' for c in COLS) + "</header>")
    parts.append('<div class="p-title">' + esc(pg["title"]) + "</div>")
    parts.append('<div class="grid">')
    parts.append('<aside class="col-cue">' + cues_html(pg["cues"]) + "</aside>")
    parts.append('<div class="col-note">' + body_html(pg["body"]) + "</div>")
    parts.append("</div>")
    if pg.get("callout"):
        parts.append('<div class="callout">' + esc(pg["callout"]).replace("\n", "<br>") + "</div>")
    parts.append('<footer class="sum">')
    parts.append('<div class="sum-label">总结</div>')
    parts.append('<div class="sum-text">' + esc(pg["summary"]) + "</div>")
    parts.append("</footer>")
    parts.append(f'<div class="pno">{idx}/{total}</div>')
    parts.append("</section>")
    return "\n".join(parts)


CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --ink: #1c1c1c;
  --ink-2: #55544f;
  --ink-3: #8d8b84;
  --rule: #cfcdc5;
  --rule-2: #e6e4dd;
  --paper: #ffffff;
  --tint: #f4f3ef;
  --accent: #6b5842;
}
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
  grid-template-columns: 26% 24% 26% 24%;
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
.grid { display: grid; grid-template-columns: 27% 73%; column-gap: 8mm; flex: 1; }
.col-cue { border-right: 1px solid var(--rule-2); padding-right: 5mm; }
.cue { margin-bottom: 7mm; }
.cue-h { font-size: 12px; font-weight: 700; color: var(--ink); line-height: 1.5; letter-spacing: .02em; }
.cue-b { font-size: 10.5px; color: var(--ink-2); line-height: 1.72; margin-top: 2px; }
.col-note { }
.dlg { font-size: 12.4px; line-height: 1.95; color: #2c2b28; margin-bottom: 3.4mm; text-align: justify; }
.who { font-weight: 700; color: var(--accent); margin-right: .5em; letter-spacing: .02em; }
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
.sum-text { font-size: 11px; line-height: 1.85; color: var(--ink-2); }
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


def build(ep):
    slug = ep["slug"]
    pages = ""

    # 封面
    pages += f"""<section class="page cover">
  <div class="cover-top">
    <div class="cover-brand">Study Room</div>
    <div class="cover-mark">Cornell Notes Series</div>
  </div>
  <div class="cover-mid">
    <div class="cover-num">{esc(ep['num'])} | {esc(ep['num_en'])}</div>
    <div class="cover-title">{esc(ep['title'])}</div>
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

    total = len(ep["pages"])
    for i, pg in enumerate(ep["pages"], 1):
        pages += page_html(pg, i, total)

    # 金句回顾
    qs = "".join(f'<div class="quote-row">{esc(q)}</div>' for q in ep["quotes"])
    pages += f"""<section class="page">
  <header class="band"><div class="band-c">本期金句回顾</div><div class="band-c"></div><div class="band-c"></div><div class="band-c"></div></header>
  <div class="nav-h">本期金句回顾</div>
  <div class="quote-list">{qs}</div>
</section>"""

    # 尾页
    pages += f"""<section class="page end-page">
  <div class="end-big">{'<br>'.join(esc(x) for x in ep['end_lines'])}</div>
  <div class="end-small">{esc(ep['tagline'])}</div>
  <div class="end-rule"></div>
  <div class="end-meta">
    自习室学习委员课堂笔记<br>
    {esc(ep['title'])} × {esc(ep['subtitle'])}<br>
    进步是最性感的事
  </div>
  <a class="back-home" href="../index.html">← 返回档案首页</a>
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
<style>{CSS}</style>
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


if __name__ == "__main__":
    from episodes_data import EPISODES
    n = 0
    for ep in EPISODES:
        if ep.get("style") != "cornell":
            continue
        mod = importlib.import_module(ep["cornell_data"])
        print("wrote", build(mod.EP), "[康奈尔笔记风格]")
        n += 1
    print(f"共 {n} 期使用康奈尔笔记风格")
