#!/usr/bin/env python3
"""QuietCast Knowledge Zine · 杂志渲染器（Quiet Editorial Reading）

用法:
    python3 gen_magazine.py spec.json OUTDIR [--shot] [--pdf]

spec.json 结构（见 templates/magazine-spec.example.json）：
{
  "title": "...", "subtitle": "...", "podcast": "...", "episode": "...",
  "source_url": "...", "source_coverage": "full_transcript", "revision": 1,
  "built_at": "2026-10-13",
  "cover": {"meta": ["教育在场", "2026-10-01", "1:51:30"], "concept": "soft-shapes"},
  "letter": {"heading": "卷首", "body": ["...", "..."], "questions": ["...", "..."]},
  "map": {"heading": "阅读地图", "items": [{"no": "01", "title": "...", "hint": "..."}]},
  "pages": [
    {"id": "P04", "type": "EXPLAIN", "label_cn": "概念机制", "question": "...",
     "title": "...", "thesis": "...", "body": ["..."],
     "diagram": {"kind": "sequence|compare|concept|none", "items": [...]},
     "sources": [{"claim_id": "c012", "ts": "48:01", "speaker": "成庆"}],
     "note_slot": true, "accent": "cream"}
  ],
  "sources_page": {"heading": "出处", "rows": [{"label": "...", "value": "..."}], "extra": ["..."]}
}

产物：magazine.html（响应式文章页）+ 可选 PDF + 可选整页截图。
"""
import argparse
import base64
import html
import json
import mimetypes
import shutil
import subprocess
from pathlib import Path

TOKENS = {
    'paper': '#F6F4EF', 'paper_alt': '#EEEBE5', 'ink': '#303532', 'ink_muted': '#626963',
    'rule': '#D8D8D0', 'cream': '#EDE1B9', 'mist_rose': '#E9D8DC',
    'dusty_lilac': '#DCD7E8', 'sage': '#D7E1D6', 'warning_ink': '#765F43',
}

# 三套色板：warm = Quiet 原版纸感；cool = 站点冷灰体系；forest = 站点森林墨水
# cool / forest 取自 zine-site 的既有定义（index.html 冷灰 + gen_zines.py 主题 t-d 森林墨水），
# 保证杂志页与站点骨架是同一套颜色，而不是另起一套。
PALETTES = {
    # ── 站点四主题（取自 zine-site/scripts/gen_zines.py 的 THEMES，逐一对应）──
    # 一期一个主题：站点 zine 页与知识杂志共用同一个主题色，读者点进来不用换眼睛。
    't-a': {  # 牛皮纸档案
        'paper': '#F5F0E8', 'paper_alt': '#EDE8DC', 'ink': '#2A2018', 'ink_muted': '#6B5344',
        'rule': '#C4B89A', 'cream': '#E8DFC8', 'mist_rose': '#E6D8CF',
        'dusty_lilac': '#DED6CD', 'sage': '#DFE0CD', 'warning_ink': '#8B2E1A',
    },
    't-b': {  # 蓝图档案（深底浅字；图卡明度比底色高两档，小字不能用灰）
        'paper': '#0D1B2A', 'paper_alt': '#14273D', 'ink': '#DCEAF8', 'ink_muted': '#CFE2F6',
        'rule': '#3A6390', 'cream': '#1E4268', 'mist_rose': '#20405E',
        'dusty_lilac': '#223F6B', 'sage': '#1B3F5C', 'warning_ink': '#7FD3FF',
    },
    't-c': {  # 油印机风
        'paper': '#FAFAF5', 'paper_alt': '#F2F2EC', 'ink': '#1A1A1A', 'ink_muted': '#6E6E6E',
        'rule': '#CCCCCC', 'cream': '#F0ECE0', 'mist_rose': '#EFE3E1',
        'dusty_lilac': '#E9E6EA', 'sage': '#E6E9E2', 'warning_ink': '#C0392B',
    },
    't-d': {  # 森林墨水
        'paper': '#F2F4EE', 'paper_alt': '#E8ECE0', 'ink': '#1E2818', 'ink_muted': '#5A6A4C',
        'rule': '#D0D8C4', 'cream': '#DFE6CF', 'mist_rose': '#E3E8DA',
        'dusty_lilac': '#D8E2CF', 'sage': '#CDDCC4', 'warning_ink': '#4A5C22',
    },
    # ── 历史变体（早期版本用过，保留以便重出旧文件）──
    'warm': TOKENS,
    'cool': {
        'paper': '#F2F4F6', 'paper_alt': '#E9EDF0', 'ink': '#1A1A1A', 'ink_muted': '#55544F',
        'rule': '#D7DDE2', 'cream': '#E4E9EC', 'mist_rose': '#E6E6EA',
        'dusty_lilac': '#E2DDEA', 'sage': '#DFE6E2', 'warning_ink': '#5A5348',
    },
    # 别名：forest = t-d，供早期 spec 与 manifest 沿用
    'forest': {
        'paper': '#F2F4EE', 'paper_alt': '#E8ECE0', 'ink': '#1E2818', 'ink_muted': '#5A6A4C',
        'rule': '#D0D8C4', 'cream': '#DFE6CF', 'mist_rose': '#E3E8DA',
        'dusty_lilac': '#D8E2CF', 'sage': '#CDDCC4', 'warning_ink': '#4A5C22',
    },
}


CSS = """
/*__ROOT__*/
/* 排版基线沿用既有电子杂志那套（深墨正文 + 衬线大标题 + 等宽标签），
   差别只在纸色由 --palette 决定：笔画要够重，禁止细体与半透明文字。 */
* { box-sizing: border-box; }
html { background: var(--paper); }
body { margin: 0; color: var(--ink);
       font-family: "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC", sans-serif;
       font-size: 19px; font-weight: 500; line-height: 1.9; letter-spacing: .01em;
       text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; }
.sheet { max-width: 760px; margin: 0 auto; padding: 0 24px 100px; }
section.page { padding: 56px 0 48px; border-top: 1px solid var(--rule); }
section.page:first-of-type { border-top: none; }
.eyebrow { display: flex; gap: 12px; align-items: baseline; font-size: 13px; font-weight: 600;
           letter-spacing: .18em; color: var(--ink-muted); text-transform: uppercase;
           font-family: "Noto Sans Mono CJK SC", "Noto Sans Mono", monospace; }
.eyebrow .cn { letter-spacing: .1em; text-transform: none; }
h1 { font-family: "Noto Serif CJK SC", "Source Han Serif SC", serif;
     font-size: 42px; line-height: 1.3; margin: 16px 0 12px; font-weight: 800; }
h2 { font-family: "Noto Serif CJK SC", "Source Han Serif SC", serif;
     font-size: 32px; line-height: 1.4; margin: 14px 0 14px; font-weight: 700; }
h3 { font-size: 22px; margin: 28px 0 10px; font-weight: 700; }
p { margin: 0 0 16px; }
.question { font-size: 17px; font-weight: 600; color: var(--ink-muted); margin: 0 0 8px; }
.thesis { background: var(--paper-alt); border-left: 4px solid var(--ink);
          padding: 16px 20px; margin: 18px 0 22px; font-size: 20px; font-weight: 600; line-height: 1.75; }
.diagram { margin: 24px 0; padding: 20px; background: var(--paper-alt); border-radius: 4px; }
.diagram .d-title { font-size: 14px; font-weight: 600; letter-spacing: .12em;
                    color: var(--ink-muted); margin-bottom: 14px;
                    font-family: "Noto Sans Mono CJK SC", monospace; }
.seq { list-style: none; padding: 0; margin: 0; }
.seq li { position: relative; padding-left: 34px; margin-bottom: 14px; }
.seq li::before { content: attr(data-no); position: absolute; left: 0; top: 4px;
                  font-size: 13px; font-weight: 600; color: var(--ink-muted);
                  font-family: "Noto Sans Mono CJK SC", monospace; }
.seq li b, .seq li strong { font-weight: 700; }
.cmp { display: flex; gap: 16px; flex-wrap: wrap; }
.cmp > div { flex: 1 1 240px; padding: 16px; border-radius: 4px;
             border: 1px solid var(--rule); }
.cmp .a { background: var(--mist-rose); }
.cmp .b { background: var(--sage); }
.cmp .k { font-size: 14px; font-weight: 700; color: var(--ink); margin-bottom: 8px; }
.pills { display: flex; flex-wrap: wrap; gap: 10px; }
.pill { padding: 8px 14px; border-radius: 999px; font-size: 17px; font-weight: 600;
        background: var(--dusty-lilac); }
.pill.cream { background: var(--cream); }
.pill.rose { background: var(--mist-rose); }
.pill.sage { background: var(--sage); }
blockquote { margin: 20px 0; padding: 18px 22px; background: var(--mist-rose);
             border-radius: 4px; font-size: 20px; font-weight: 600; line-height: 1.8; }
blockquote cite { display: block; margin-top: 12px; font-style: normal; font-size: 14px;
                  font-weight: 500; color: var(--ink-muted);
                  font-family: "Noto Sans Mono CJK SC", monospace; }
.src { font-size: 15px; font-weight: 500; color: var(--ink-muted); margin-top: 12px; }
.warn { color: var(--warning-ink); font-weight: 600; }
.slot { margin-top: 22px; padding: 16px 18px; border: 1px dashed var(--rule);
        border-radius: 4px; font-size: 15px; color: var(--ink-muted); background: transparent; }
.cover { padding-top: 76px; }
.cover h1 { font-size: 54px; }
.cover .sub { font-size: 22px; font-weight: 500; color: var(--ink-muted); margin-bottom: 28px; }
.sitebar { position: sticky; top: 0; z-index: 9; background: var(--paper);
           border-bottom: 1px solid var(--rule); padding: 10px 24px; font-size: 14px; }
.sitebar-inner { max-width: 760px; margin: 0 auto; }
.sitebar a { color: var(--ink-muted); text-decoration: none; font-weight: 500; }
.sitebar a:hover { color: var(--ink); }
.sitebar .sep { margin: 0 8px; color: var(--rule); }
.footnav { margin-top: 44px; padding-top: 24px; border-top: 1px solid var(--rule);
           display: flex; gap: 24px; flex-wrap: wrap; align-items: baseline; }
.footnav a { font-family: "Noto Sans Mono CJK SC", "Noto Sans Mono", monospace; font-size: 13px;
             letter-spacing: .16em; color: var(--warning-ink); text-decoration: none;
             border-bottom: 1px solid currentColor; padding-bottom: 2px; }
.footnav a:hover { opacity: .7; }
.footnav .fine { margin-left: auto; font-size: 12px; color: var(--ink-muted); }
.coverimg { margin: 28px 0 24px; border-radius: 6px; overflow: hidden;
            background: var(--paper-alt); text-align: center; }
.coverimg img { display: block; width: 100%; height: auto; max-height: 62vh; object-fit: contain; }
.concept { height: 220px; margin: 28px 0 24px; border-radius: 6px; position: relative;
           overflow: hidden; background: var(--paper-alt); }
.concept i { position: absolute; border-radius: 50%; display: block; }
.concept .s1 { width: 200px; height: 200px; background: var(--cream); left: 6%; top: 12%; }
.concept .s2 { width: 156px; height: 156px; background: var(--sage); left: 40%; top: 34%; }
.concept .s3 { width: 126px; height: 126px; background: var(--dusty-lilac); right: 10%; top: 8%; }
.concept .s4 { width: 96px; height: 96px; background: var(--mist-rose); right: 24%; bottom: 8%; }
.meta { font-size: 15px; font-weight: 500; color: var(--ink-muted);
        font-family: "Noto Sans Mono CJK SC", monospace; letter-spacing: .08em; }
.mapitem { display: flex; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--rule); }
.mapitem .no { font-size: 14px; font-weight: 600; color: var(--ink-muted); padding-top: 5px;
               min-width: 30px; font-family: "Noto Sans Mono CJK SC", monospace; }
.mapitem .t { font-size: 20px; font-weight: 700; }
.mapitem .h { font-size: 15px; color: var(--ink-muted); font-weight: 500; }
footer.sources { font-size: 15px; font-weight: 500; color: var(--ink-muted); }
footer.sources .row { display: flex; gap: 14px; padding: 9px 0;
                      border-bottom: 1px solid var(--rule); }
footer.sources .row .l { min-width: 140px; color: var(--ink); font-weight: 700; }
@media (max-width: 520px) { body { font-size: 18px; } h1 { font-size: 34px; }
                            h2 { font-size: 26px; } .cover h1 { font-size: 38px; } }
@page { size: A5; margin: 14mm 13mm 15mm; }
@media print {
  /* A5 上不要把网页字号等比缩小：用 pt 重新给一套，保证墨色与字号到位 */
  body { font-size: 11.8pt; line-height: 1.8; }
  .sheet { max-width: none; padding: 0; }
  section.page { break-after: page; border-top: none; padding: 0; }
  section.page > h1, section.page > .eyebrow { margin-top: 0; }
  h1 + .sub, h1 + .q { margin-top: 1.5mm; }
  .diagram { margin: 4mm 0 3mm; }
  /* 图表与笔记区不跨页拆开：标题和方框分到两页会读断 */
  .diagram, .slot, blockquote, .cmp, .mapitem { break-inside: avoid; page-break-inside: avoid; }
  h2, .thesis { break-after: avoid; page-break-after: avoid; }
  .diagram .d-title { margin-bottom: 1.5mm; }
  footer.sources .row { padding: 5px 0; }
  section.page:last-of-type { break-after: auto; }
  h1 { font-size: 22.9pt; } h2 { font-size: 17.1pt; } h3 { font-size: 13.5pt; }
  .cover h1 { font-size: 31pt; } .cover .sub { font-size: 13pt; }
  .thesis { font-size: 13pt; } blockquote { font-size: 13pt; }
  .eyebrow, .diagram .d-title, .meta, .src, .slot, blockquote cite,
  footer.sources, .cmp .k, .mapitem .h { font-size: 9.5pt; }
  .mapitem .t { font-size: 13pt; }
  .concept { height: 50mm; }
  .footnav { margin-top: 10mm; }
  .coverimg { margin: 6mm 0; }
  .coverimg img { max-height: 92mm; }
  .sitebar { display: none !important; }   /* 粘性站点条不进纸版 */
  a { color: inherit; text-decoration: none; }
}
"""


def esc(s):
    return html.escape(str(s))


def paras(items):
    return "".join(f"<p>{esc(x)}</p>" for x in items or [])


def eyebrow(page):
    bits = [f'<span>{esc(page.get("id", ""))}</span>']
    if page.get('type'):
        bits.append(f'<span>{esc(page["type"])}</span>')
    if page.get('label_cn'):
        bits.append(f'<span class="cn">{esc(page["label_cn"])}</span>')
    return f'<div class="eyebrow">{"".join(bits)}</div>'


def diagram(d):
    if not d or d.get('kind') in (None, 'none'):
        return ""
    kind = d['kind']
    head = f'<div class="d-title">{esc(d.get("title", ""))}</div>'
    if kind == 'sequence':
        lis = "".join(
            f'<li data-no="{esc(i.get("no", f"{n+1:02d}"))}"><b>{esc(i.get("t",""))}</b>'
            + (f'　{esc(i["d"])}' if i.get('d') else '') + '</li>'
            for n, i in enumerate(d.get('items', [])))
        return f'<div class="diagram">{head}<ol class="seq">{lis}</ol></div>'
    if kind == 'compare':
        a, b = d.get('left', {}), d.get('right', {})
        return (f'<div class="diagram">{head}<div class="cmp">'
                f'<div class="a"><div class="k">{esc(a.get("k",""))}</div>{paras(a.get("body",[]))}</div>'
                f'<div class="b"><div class="k">{esc(b.get("k",""))}</div>{paras(b.get("body",[]))}</div>'
                f'</div></div>')
    if kind == 'concept':
        pills = "".join(
            f'<span class="pill {esc(i.get("accent",""))}">{esc(i.get("t",""))}</span>'
            for i in d.get('items', []))
        return f'<div class="diagram">{head}<div class="pills">{pills}</div>'
    if kind == 'quote':
        q = d.get('quote', {})
        return (f'<blockquote>{esc(q.get("text",""))}'
                f'<cite>{esc(q.get("who",""))}{("　" + esc(q["ts"])) if q.get("ts") else ""}</cite>'
                f'</blockquote>')
    return ""


def page_html(p):
    out = ['<section class="page">', eyebrow(p)]
    if p.get('question'):
        out.append(f'<div class="question">{esc(p["question"])}</div>')
    if p.get('title'):
        out.append(f'<h2>{esc(p["title"])}</h2>')
    if p.get('thesis'):
        out.append(f'<div class="thesis">{esc(p["thesis"])}</div>')
    out.append(paras(p.get('body')))
    out.append(diagram(p.get('diagram')))
    if p.get('sources'):
        chips = "、".join(
            f'{esc(s.get("claim_id",""))}'
            + (f'（{esc(s["speaker"])}，{esc(s["ts"])}）' if s.get('ts') else f'（{esc(s.get("speaker",""))}）')
            for s in p['sources'])
        out.append(f'<div class="src">来源：{chips}</div>')
    if p.get('note_slot'):
        out.append('<div class="slot">个人笔记本页：这里留给你写自己的观察、反例和想追问的问题。</div>')
    out.append('</section>')
    return "\n".join(x for x in out if x)


def root_css(palette):
    t = PALETTES.get(palette) or PALETTES['warm']
    pairs = [('--paper', t['paper']), ('--paper-alt', t['paper_alt']), ('--ink', t['ink']),
             ('--ink-muted', t['ink_muted']), ('--rule', t['rule']), ('--cream', t['cream']),
             ('--mist-rose', t['mist_rose']), ('--dusty-lilac', t['dusty_lilac']),
             ('--sage', t['sage']), ('--warning-ink', t['warning_ink'])]
    body = ' '.join(f'{k}:{v};' for k, v in pairs)
    return f':root {{ {body} }}'


def build(spec):
    css = CSS.replace('/*__ROOT__*/', root_css(spec.get('palette', 'warm')))
    home = spec.get('home_link', '../../../index.html')
    notes = spec.get('notes_link', './notes.html')
    pdf = spec.get('pdf_link', './magazine.pdf')
    s = [f'<div class="sheet">']
    cov = spec.get('cover', {})
    s.append('<section class="page cover">')
    s.append(f'<div class="eyebrow"><span>QUIETCAST</span><span class="cn">声音成册</span>'
             f'<span>REV {spec.get("revision", 1)}</span></div>')
    s.append(f'<h1>{esc(spec.get("title",""))}</h1>')
    s.append(f'<div class="sub">{esc(spec.get("subtitle",""))}</div>')
    img = spec.get('cover_image')
    if img:
        alt = esc(spec.get('cover_alt') or f"{spec.get('podcast','')} {spec.get('episode','')}")
        s.append(f'<figure class="coverimg"><img src="{esc(img)}" alt="{alt}"></figure>')
    else:
        s.append('<div class="concept"><i class="s1"></i><i class="s2"></i><i class="s3"></i><i class="s4"></i></div>')
    meta = cov.get('meta') or []
    s.append('<div class="meta">' + "　·　".join(esc(x) for x in meta) + '</div>')
    s.append('</section>')

    letter = spec.get('letter')
    if letter:
        s.append('<section class="page"><div class="eyebrow"><span>LETTER</span>'
                 f'<span class="cn">{esc(letter.get("heading","卷首"))}</span></div>')
        s.append(paras(letter.get('body')))
        if letter.get('questions'):
            s.append('<h3>读完希望回答的问题</h3><ul class="seq">')
            for n, q in enumerate(letter['questions']):
                s.append(f'<li data-no="{n+1:02d}">{esc(q)}</li>')
            s.append('</ul>')
        s.append('</section>')

    mp = spec.get('map')
    if mp:
        s.append('<section class="page"><div class="eyebrow"><span>MAP</span>'
                 f'<span class="cn">{esc(mp.get("heading","阅读地图"))}</span></div>')
        for i in mp.get('items', []):
            s.append('<div class="mapitem">'
                     f'<div class="no">{esc(i.get("no",""))}</div>'
                     f'<div><div class="t">{esc(i.get("title",""))}</div>'
                     f'<div class="h">{esc(i.get("hint",""))}</div></div></div>')
        s.append('</section>')

    for p in spec.get('pages', []):
        s.append(page_html(p))

    src = spec.get('sources_page')
    if src:
        s.append('<section class="page"><div class="eyebrow"><span>SOURCES</span>'
                 f'<span class="cn">{esc(src.get("heading","出处"))}</span></div>')
        s.append('<footer class="sources">')
        for r in src.get('rows', []):
            s.append(f'<div class="row"><div class="l">{esc(r.get("label",""))}</div>'
                     f'<div>{esc(r.get("value",""))}</div></div>')
        s.append('</footer>')
        if src.get('extra'):
            s.append('<h3>制作说明</h3>' + paras(src['extra']))
        # 页尾固定返回区（与站点 zine 页的 back-home 同一规矩：每份杂志页尾都要有回首页的键）
        # 放在最后一节里面，跟出处页同页，不单独占一页
        s.append('<footer class="footnav">'
                 f'<a href="{esc(home)}">← 返回首页</a>'
                 f'<a href="{esc(notes)}">知识笔记</a>'
                 f'<a href="{esc(pdf)}">下载 PDF</a>'
                 f'<span class="fine">QUIETCAST · REV {esc(str(spec.get("revision", 1)))}</span>'
                 '</footer>')
        s.append('</section>')
    s.append('</div>')
    body = ('<div class="sitebar"><div class="sitebar-inner">'
            f'<a href="{esc(home)}">← 播客知识库</a><span class="sep">/</span>'
            f'<a href="{esc(notes)}">知识笔记</a><span class="sep">/</span>'
            f'<a href="{esc(pdf)}">PDF</a></div></div>' + "\n".join(s))
    return (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(spec.get("title",""))}</title><style>{css}</style></head>'
            f'<body>{body}</body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('outdir')
    ap.add_argument('--shot', action='store_true', help='整页截图 preview.png')
    ap.add_argument('--pdf', action='store_true', help='打印为 magazine.pdf（A5）')
    ap.add_argument('--chrome', default='google-chrome')
    ap.add_argument('--palette', choices=list(PALETTES), default=None,
                    help='覆盖 spec 里的 palette（站点四主题 t-a..t-d，另有历史变体 warm/cool/forest）')
    a = ap.parse_args()
    spec_path = Path(a.spec)
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    if a.palette:
        spec['palette'] = a.palette
    img = spec.get('cover_image')
    if img and not str(img).startswith(('http://', 'https://', 'data:')):
        src = Path(img)
        if not src.is_absolute():
            src = spec_path.parent / src
        if src.exists():
            mime = mimetypes.guess_type(str(src))[0] or 'image/jpeg'
            spec['cover_image'] = ('data:' + mime + ';base64,'
                                   + base64.b64encode(src.read_bytes()).decode('ascii'))
            dst = Path(a.outdir) / 'assets'
            dst.mkdir(parents=True, exist_ok=True)
            if src.resolve() != (dst / src.name).resolve():
                shutil.copy(src, dst / src.name)
            print(f'[IMG ] {src} -> 内联 data URI，并复制到 {dst / src.name}')
        else:
            print(f'[WARN] 封面图不存在：{src}（该页退回抽象色块）')
            spec.pop('cover_image', None)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    html_path = out / 'magazine.html'
    html_path.write_text(build(spec), encoding='utf-8')
    print(f'[HTML] {html_path}')
    if a.pdf:
        pdf = out / 'magazine.pdf'
        subprocess.run([a.chrome, '--headless', '--disable-gpu', '--no-sandbox',
                        '--no-pdf-header-footer', f'--print-to-pdf={pdf.resolve()}',
                        html_path.resolve().as_uri()], check=True, capture_output=True)
        print(f'[PDF ] {pdf}')
    if a.shot:
        png = out / 'preview.png'
        subprocess.run([a.chrome, '--headless', '--disable-gpu', '--no-sandbox',
                        '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--window-size=900,2600', f'--screenshot={png.resolve()}',
                        html_path.resolve().as_uri()], check=True, capture_output=True)
        print(f'[PNG ] {png}')


if __name__ == '__main__':
    main()
