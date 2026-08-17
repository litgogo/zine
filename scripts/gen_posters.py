#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 14 期 Minimal Zine Poster 封面 (3:5 竖版) - 按 gc-minimal-zine-poster-v0-1 规范"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from episodes_data import EPISODES

OUT = os.path.expanduser('~/.hermes/workspace/zine-site/posters')
os.makedirs(OUT, exist_ok=True)

# 高饱和色锚点 (cobalt/lemon/magenta/green/orange/tomato/indigo/ochre/brick/pink/violet/skyblue/leafgreen/ultramarine)
COLORS = {
    "cobalt":    ("#2f4fd8", "钴蓝"),
    "lemon":     ("#f2c400", "柠檬黄"),
    "magenta":   ("#d6318a", "品红"),
    "green":     ("#2ea34b", "翠绿"),
    "orange":    ("#e8651a", "焦橙"),
    "tomato":    ("#d8402f", "番茄红"),
    "indigo":    ("#3d3f9e", "靛蓝"),
    "ochre":     ("#c08a2d", "赭石"),
    "brick":     ("#a63d2a", "砖红"),
    "pink":      ("#e08aa8", "樱粉"),
    "violet":    ("#7a4fb0", "紫罗兰"),
    "skyblue":   ("#3a9ad0", "天蓝"),
    "leafgreen": ("#4f9a3f", "叶绿"),
    "ultramarine":("#1b3fa8", "群青"),
}

def render(ep):
    slug = ep["slug"]
    color_hex, color_name = COLORS[ep["poster"]["color"]]
    line = ep["poster"]["line"]
    metaphor = ep["poster"]["metaphor"]
    show = ep["show"]
    date = ep["date"]
    vol = ep["vol"]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>{slug}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;600;900&family=Noto+Sans+Mono&family=Dancing+Script:wght@700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:1200px; height:2000px; overflow:hidden; background:#f2efe8; font-family:'Noto Serif SC', serif; }}
/* 旧纸质感 */
.paper {{
  position:absolute; inset:0;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(180,160,130,.10), transparent 60%),
    radial-gradient(ellipse at 75% 80%, rgba(150,130,100,.08), transparent 55%),
    linear-gradient(180deg, #f4f1ea 0%, #efece4 100%);
}}
.paper::after {{
  content:''; position:absolute; inset:0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.05 0'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity:.5; mix-blend-mode:multiply;
}}
/* 大留白 + 锚点区 */
.anchor {{
  position:absolute; top:38%; left:50%; transform:translate(-50%,-50%);
  width:340px; height:340px;
}}
/* 锚点图形: 圆 + 色块 + 文字隐喻 */
.circle {{
  width:340px; height:340px; border-radius:50%;
  background:{color_hex}; opacity:.92;
  display:flex; align-items:center; justify-content:center;
}}
.circle-inner {{
  width:150px; height:150px; border-radius:50%;
  background:#f2efe8; opacity:.92;
  display:flex; align-items:center; justify-content:center;
  font-family:'Noto Serif SC'; font-weight:900; font-size:22px; color:#2a2a26; letter-spacing:.1em;
}}
/* 顶部小字: 节目+日期 */
.top-meta {{
  position:absolute; top:70px; left:80px; right:80px;
  display:flex; justify-content:space-between;
  font-family:'Noto Sans Mono'; font-size:17px; letter-spacing:.28em; color:#6b6558; text-transform:uppercase;
}}
/* 底部大字: 隐喻句 */
.bottom-line {{
  position:absolute; bottom:180px; left:80px; right:80px;
  font-family:'Dancing Script'; font-size:44px; color:#2a2a26; text-align:center; letter-spacing:.02em;
}}
.bottom-sub {{
  position:absolute; bottom:120px; left:80px; right:80px;
  font-family:'Noto Sans Mono'; font-size:15px; letter-spacing:.2em; color:#8a8474; text-align:center;
}}
.vol {{
  position:absolute; top:70px; right:80px;
  font-family:'Noto Sans Mono'; font-size:15px; letter-spacing:.24em; color:#8a8474;
}}
/* 散落微文字（档案感） */
.drift {{
  position:absolute; font-family:'Noto Sans Mono'; font-size:13px; letter-spacing:.3em; color:#a29a88; opacity:.7;
}}
.d1 {{ top:250px; left:110px; transform:rotate(-6deg); }}
.d2 {{ top:300px; right:100px; transform:rotate(4deg); }}
.d3 {{ bottom:320px; left:120px; transform:rotate(3deg); }}
.d4 {{ bottom:360px; right:110px; transform:rotate(-5deg); }}
</style></head>
<body>
<div class="paper"></div>
<div class="top-meta"><span>{show}</span></div>
<span class="vol">{vol}</span>
<span class="drift d1">声 · {date}</span>
<span class="drift d2">{color_name}</span>
<span class="drift d3">ARCHIVE</span>
<span class="drift d4">手记 · NOTES</span>
<div class="anchor"><div class="circle"><div class="circle-inner">{metaphor}</div></div></div>
<div class="bottom-line">{line}</div>
<div class="bottom-sub">PODCAST ARCHIVE · {date}</div>
</body></html>
"""
    path = os.path.join(OUT, f"{slug}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

if __name__ == "__main__":
    for ep in EPISODES:
        p = render(ep)
        print(f"wrote {p}")
