#!/usr/bin/env python3
"""Cyberpunk talking-head template: build <run>/index.html from <run>/scenes.json.
usage: build.py <run-dir> [--refresh]   (--refresh re-copies style.css / timeline.js / fonts / cjk files from the template)
Text markup in scenes.json strings: \\n = line break, {ec:X} cyan English name, {en:X} English font,
{kw:X} red keyword (titles), {kwen:X} red English keyword, {y:X} yellow keyword (cards), {hl:X} turns yellow when the task is active,
{c:X} cyan, {r:X} red. Raw HTML passes through."""
import json, sys, os, re, shutil
T = os.path.dirname(os.path.abspath(__file__)); run = os.path.abspath(sys.argv[1]); S = json.load(open(f'{run}/scenes.json'))
for f in ('style.css', 'timeline.js', 'cjk-captions.css', 'cjk-captions.js', 'fonts'):
    src, dst = f'{T}/{f}', f'{run}/{f}'
    if '--refresh' in sys.argv or not os.path.exists(dst):
        if os.path.isdir(src): shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
        else: shutil.copy(src, dst)
def mk(s):
    s = re.sub(r'\[(kwen|ec|en|kw|y|hl|c|r)\](.*?)\[/\1\]', r'{\1:\2}', s)   # also accept [kw]..[/kw] (cover style)
    for k, cls in (('kwen', 'en kw'), ('ec', 'en cy'), ('en', 'en'), ('kw', 'kw'), ('y', 'y yl'), ('hl', 'hl'), ('c', 'cy'), ('r', 'rd')):
        s = re.sub(r'\{' + k + r':([^}]*)\}', rf'<span class="{cls}">\1</span>', s)
    return s.replace('\n', '<br>')
R = lambda o: o.get('ranges') or f"{o['t0']}-{o.get('t1', 999)}"
out = []
A = out.append
A('<!doctype html>\n<meta charset="utf-8">\n<link rel="stylesheet" href="safe-zone.css">\n<link rel="stylesheet" href="fonts/fonts.css">\n<link rel="stylesheet" href="cjk-captions.css">\n<link rel="stylesheet" href="style.css">')
A('<div id="stage" data-safe-zone="9:16" data-stateless>\n  <div id="grid"></div>\n  <div id="media">')
for sc in S['scenes']:
    c = sc.get('case')
    if not c: continue
    fr = c.get('frame', {}); top, h = fr.get('top', 430), fr.get('height', 591)
    A(f'  <div class="scene" data-ranges="{sc["t0"]}-{sc["t1"]}">')
    A(f'    <div class="frame cut" style="left:40px;top:{top}px;width:1000px;height:{h}px"><div class="in cut" style="{fr.get("bg", "")}">')
    for it in c.get('items', []):
        rg = f' data-ranges="{it["ranges"]}"' if 'ranges' in it else ''
        if 'video' in it:
            A(f'      <video src="{it["video"]}" muted data-at="{it.get("at", sc["t0"])}" data-rate="{it.get("rate", 1)}"{rg}></video>')
        else:
            kf = f' data-kf="{it["kf"]}"' if 'kf' in it else ''
            style = it.get('style', '')
            cls = '' if style else ' class="fill"'
            A(f'      <img{cls} src="{it["image"]}" style="{style}{";transform-origin:0 0" if kf else ""}"{kf}{rg}>')
    for b in c.get('inner_boxes', []):
        A(f'      <div class="abs" style="left:{b["x"]}px;top:{b["y"]}px;width:{b["w"]}px;height:{b["h"]}px;border:4px solid var(--red)" data-ranges="{R(b)}" data-fx="pop"></div>')
    A('      <div class="scan"></div></div></div>')
    for b in c.get('boxes', []):
        A(f'    <div class="abs" style="left:{b["x"]}px;top:{b["y"]}px;width:{b["w"]}px;height:{b["h"]}px;border:{b.get("bw", 3)}px solid var(--red)" data-ranges="{R(b)}" data-fx="{b.get("fx", "none")}"></div>')
    for n in c.get('insets', []):
        A(f'    <div class="frame" style="left:{n["x"]}px;top:{n["y"]}px;width:{n["w"]}px;height:{n["h"]}px;background:var(--red);padding:4px" data-ranges="{R(n)}" data-fx="pop"><div class="in"><video src="{n["video"]}" muted data-at="{n.get("at", sc["t0"])}" data-rate="{n.get("rate", 1)}"></video></div></div>')
        if n.get('tag'): A(f'    <div class="tag c" style="left:{n["x"]}px;top:{n["y"] - 48}px" data-ranges="{R(n)}">{n["tag"]}</div>')
    for g in c.get('tags', []):
        big = ";font-size:49px;letter-spacing:0;font-family:'PingFang SC';font-weight:700" if g.get('big') else ''
        A(f'    <div class="tag {g.get("color", "c")}" style="left:{g["x"]}px;top:{g["y"]}px{big}" data-ranges="{R(g) if ("t0" in g or "ranges" in g) else str(sc["t0"]) + "-" + str(sc["t1"])}" data-fx="{"pop" if g.get("pop") else "none"}">{g["text"]}</div>')
    A('  </div>')
A('  </div>\n  <img class="stkghost r" id="stkg1" alt=""><img class="stkghost c" id="stkg2" alt=""><img id="stk" alt="">')
A(f'  <div id="hud" class="mono"><span>■ {S.get("hud", "OPENEDIT // CYBERPUNK")}</span><span>')
for sc in S['scenes']:
    if sc.get('hud'):
        txt = sc['hud'].replace('{n}', '<span class="rd" id="objn">0</span>')
        A(f'    <b data-ranges="{sc.get("hudRanges", str(sc["t0"]) + "-" + str(sc["t1"]))}" style="font-weight:400"{" class=rd" if sc.get("hudRed") else ""}>{txt}</b>')
A('  </span></div>\n  <div data-safe>')
for t in S.get('titles', []):
    h = mk(t['html']); fx = t.get('fx', 'ghost')
    A(f'    <div class="blk title zh rgb gw" style="top:{t.get("top", 0)}px" data-ranges="{R(t)}" data-fx="{fx}"><div class="gh r">{h}</div><div class="gh c">{h}</div><div class="main">{h}</div></div>')
for c in S.get('cards', []):
    style = f'font-size:{c["size"]}px' if 'size' in c else ''
    style += ';' + c['style'] if 'style' in c else ''
    lbl = f'<span class="lbl{" rd" if c.get("red") else ""}">{c["lbl"]}</span>' if c.get('lbl') else ''
    card = f'<div class="card{" red" if c.get("red") else ""} cut2"><div class="in cut2{" " + c["cls"] if c.get("cls") else ""}" style="{style}">{lbl}{mk(c["html"])}</div></div>'
    A(f'    <div class="blk" style="top:{c["top"]}px" data-ranges="{R(c)}" data-fx="{c.get("fx", "up")}"><div class="cardghost">{card}</div>{card}</div>')
tk = S.get('tasks')
if tk:
    A(f'    <div class="blk" id="tasks" style="top:{tk.get("top", 200)}px" data-ranges="{tk["ranges"]}">')
    for i, it in enumerate(tk['items']):
        subs = ''.join(f'<div class="sub" data-ranges="{r}">{mk(x)}</div>' for r, x in it.get('subs', []))
        A(f'      <div class="task cut2" data-in="{round(tk["appear"] + i * 0.2, 2)}" data-fx="up" data-on="{it["on"]}"><div class="in cut2"><span class="no">{i + 1:02d}</span>{mk(it["text"])}{subs}</div></div>')
    A('    </div>')
A(f'    <div data-captions data-lines="2" data-key-words="{S.get("keyWords", "")}"></div>\n  </div>\n  <div id="glitch"></div>\n</div>')
cfg = {'frames': S['frames'], 'fps': S.get('fps', 30), 'sticker': S.get('sticker', {}), 'scenes': [[s['t0'], s['t1'], s['mode']] for s in S['scenes']]}
A(f'<script>window.SCENES = {json.dumps(cfg, ensure_ascii=False)};</script>\n<script src="captions.js"></script>\n<script src="cjk-captions.js"></script>\n<script src="timeline.js"></script>')
open(f'{run}/index.html', 'w').write('\n'.join(out) + '\n')
print('wrote', f'{run}/index.html', len(S['scenes']), 'scenes', len(S.get('titles', [])), 'titles', len(S.get('cards', [])), 'cards')
