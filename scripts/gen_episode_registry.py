#!/usr/bin/env python3
"""生成 episode 注册表：每一期一个稳定 episode_id，三种版本都挂在它下面。

数据来源（只读）：
  - wall-data.js 的 WALL（电子杂志／康奈尔／知识杂志的落位与收听日）
  - scripts/episodes_data.py 的 EPISODES（期号、嘉宾、时长、标题）
  - 03-data/podcast-kb/episodes/ 目录（知识库单集档案，按节目名+关键词做最佳匹配）
输出：~/.hermes/workspace/03-data/podcast-kb/episode-registry.json

episode_id 约定：<节目短名>-<期号或主题短名>，全小写连字符；
由 slug 去掉收听日前缀得到，一经落定不再随收听日变化。
"""
import json, re, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from episodes_data import EPISODES  # noqa

WALL = json.loads('[' + '\n'.join(re.findall(r'\{[^\n]*\}', (ROOT / 'wall-data.js').read_text(encoding='utf-8'))[:0] or ['{}']) + ']') if False else None

def load_wall():
    t = (ROOT / 'wall-data.js').read_text(encoding='utf-8')
    block = t[t.index('var WALL = ['):]
    block = block[:block.index('];')]
    rows = re.findall(r'\{[^\n]*\}', block)
    return [json.loads(r) for r in rows]

def kb_match(show, title, files):
    keys = [k for k in re.split(r'[：:｜|、，,\s]+', title) if len(k) >= 2][:3]
    hits = []
    for f in files:
        if not f.endswith('.md'):
            continue
        if show.split()[0][:2] not in f and show[:4] not in f:
            continue
        if any(k[:4] in f for k in keys):
            hits.append('episodes/' + f)
    return hits

def main():
    wall = load_wall()
    eps = {e.get('eid'): e for e in EPISODES}
    kbdir = Path.home() / '.hermes/workspace/03-data/podcast-kb/episodes'
    files = sorted(p.name for p in kbdir.glob('*.md')) if kbdir.exists() else []
    reg = []
    for w in wall:
        eid = w.get('eid')
        if not eid:
            continue
        e = eps.get(eid, {})
        versions = {}
        if w.get('link'):
            versions['zine'] = w['link']
        if w.get('quiet'):
            versions['quiet'] = w['quiet']
        if w.get('deep'):
            versions['cornell' if w.get('deep_style') == 'cornell' else 'deep'] = w['deep']
        kbs = kb_match(w.get('show', ''), w.get('title', ''), files)
        if kbs:
            versions['kb'] = kbs if len(kbs) > 1 else kbs[0]
        reg.append({
            'eid': eid,
            'show': w.get('show'),
            'ep': w.get('ep') or '',
            'guest': (e.get('guest') or w.get('guest') or ''),
            'listen_date': w.get('date'),
            'title': w.get('title'),
            'core': e.get('core', ''),
            'versions': versions,
            'version_count': len(versions),
        })
    out = Path.home() / '.hermes/workspace/03-data/podcast-kb/episode-registry.json'
    out.write_text(json.dumps({'count': len(reg), 'items': reg}, ensure_ascii=False, indent=1), encoding='utf-8')
    multi = [r for r in reg if r['version_count'] > 1]
    print(f'注册表写出 {out}｜共 {len(reg)} 期｜多版本 {len(multi)} 期')
    for r in multi:
        print('  ', r['eid'], '→', ' + '.join(r['versions'].keys()))
    no_base = [r for r in reg if 'zine' not in r['versions']]
    print(f'缺基础归档（无电子杂志，只有深读版）：{len(no_base)} 期')
    for r in no_base:
        print('  ', r['eid'], r['show'], '→', '+'.join(r['versions'].keys()))

if __name__ == '__main__':
    main()
