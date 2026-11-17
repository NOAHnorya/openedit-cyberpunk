#!/usr/bin/env python3
"""Cyberpunk cover template: cover.json -> 4 layouts x {3:4 1080x1440, 4:3 1440x1080}.

usage:
  python3 build_covers.py <cover.json> <out_dir> [--render] [--only v1,v3]

Title markup inside any text field:
  [kw]...[/kw]  red keyword        [en]...[/en]  Rajdhani English name (cyan in titles)
  [sub]...[/sub] white text inside a title
Titles are acid yellow; each title line shrinks itself to fit its column (data-maxw).
Asset paths in the json are absolute or relative to the json file. Everything the pages need
(cover.css, fonts/, assets/) is copied into <out_dir>, so the folder renders on its own.
"""
import json, os, re, shutil, subprocess, sys, html
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), 'fonts')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # templates/cyberpunk/cover -> repo root
OPENEDIT = os.path.join(ROOT, 'node_modules', '.bin', 'openedit')
LABELS = {'v1': '主视觉', 'v2': '对比', 'v3': '物体手势', 'v4': '清单'}


def mk(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\[kw\](.*?)\[/kw\]', r'<span class="kw">\1</span>', s)
    s = re.sub(r'\[en\](.*?)\[/en\]', r'<span class="en" style="font-size:1.07em">\1</span>', s)
    s = re.sub(r'\[sub\](.*?)\[/sub\]', r'<span class="sub">\1</span>', s)
    return s


def title(lines, left, top, size, maxw, lh=1.08, extra=''):
    out, y = [], top
    for ln in lines:
        out.append(f'<div class="abs zh title" data-maxw="{maxw}" style="left:{left}px;top:{y}px;font-size:{size}px;width:max-content;{extra}">{mk(ln)}</div>')
        y += int(size * lh * 1.02)
    return '\n'.join(out)


def frame(w, h, inner, hud, hud_right=''):
    right = f'<div class="lab" style="right:110px;top:44px">{html.escape(hud_right)}</div>' if hud_right else ''
    return f'''<div id="stage" style="width:{w}px;height:{h}px">
<div class="grid"></div>
{inner}
<i class="brk tl" style="left:28px;top:28px"></i><i class="brk tr" style="right:28px;top:28px"></i><i class="brk bl" style="left:28px;bottom:28px"></i><i class="brk br" style="right:28px;bottom:28px"></i>
<div class="lab" style="left:110px;top:44px">{html.escape(hud)}</div>{right}
<div class="scan"></div><div class="vig"></div></div>'''


FIT = '''<script>
window.__seek = async () => {
  if (window.__fitted) return; await document.fonts.ready;
  for (const el of document.querySelectorAll('[data-maxw]')) {
    let s = parseFloat(getComputedStyle(el).fontSize); const max = +el.dataset.maxw;
    while (el.scrollWidth > max && s > 40) { s -= 2; el.style.fontSize = s + 'px'; }
  }
  window.__fitted = true;
};
</script>'''
HEAD = '<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="fonts/fonts.css"><link rel="stylesheet" href="cover.css">\n'


def build(cfg, A, obj_ratio):
    hud, P = cfg.get('hud', 'SHARE'), {}
    pm, pa, pg = A['p_main'], A.get('p_alt', A['p_main']), A.get('p_gesture', A['p_main'])

    c = cfg['v1']
    P['v1-34'] = frame(1080, 1440, f'''
<div class="beam r" style="left:-120px;top:980px;width:1500px;transform:rotate(-28deg)"></div>
<div class="beam c" style="left:-200px;top:760px;width:1600px;transform:rotate(-28deg);opacity:.8"></div>
<img class="person" src="{pm}" style="left:-150px;bottom:-30px;width:1380px">
{title(c['title_34'], 70, 110, 118, 950)}
<div class="badge r" style="left:70px;top:1210px;font-size:52px">{mk(c['badge'])}</div>''', hud, c.get('hud_right', ''))
    P['v1-43'] = frame(1440, 1080, f'''
<div class="beam r" style="left:520px;top:900px;width:1300px;transform:rotate(-30deg)"></div>
<div class="beam c" style="left:420px;top:760px;width:1300px;transform:rotate(-30deg);opacity:.8"></div>
<img class="person" src="{pm}" style="left:600px;bottom:-30px;width:1240px">
{title(c['title_43'], 80, 150, 132, 560)}
<div class="badge r" style="left:80px;top:850px;font-size:50px">{mk(c['badge'])}</div>''', hud, c.get('hud_right', ''))

    c = cfg['v2']
    def wins(x, y, w, h):
        return f'''
<div class="win" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:var(--red)"><div><img src="{A['compare_left']}"></div></div>
<div class="badge r" style="left:{x}px;top:{y - 70}px;font-size:44px">{mk(c['left_label'])}</div>
<div class="win" style="left:{x + w + 40}px;top:{y}px;width:{w}px;height:{h}px;background:var(--cy)"><div><img src="{A['compare_right']}"></div></div>
<div class="badge c" style="left:{x + w + 40}px;top:{y - 70}px;font-size:44px">{mk(c['right_label'])}</div>
<div class="abs en vs" style="left:{x + w - 34}px;top:{y + h // 2 - 60}px;font-size:96px">VS</div>'''
    P['v2-34'] = frame(1080, 1440, title(c['title_34'], 70, 100, 104, 950) + wins(60, 420, 460, 400) +
                       f'\n<img class="person" src="{pm}" style="left:150px;bottom:-30px;width:800px">', hud, c.get('hud_right', ''))
    P['v2-43'] = frame(1440, 1080, title(c['title_43'], 80, 100, 104, 1280) + wins(80, 400, 400, 520) +
                       f'\n<img class="person" src="{pm}" style="left:860px;bottom:-30px;width:760px">', hud, c.get('hud_right', ''))

    c = cfg['v3']
    def obj(x, y, w):
        h = int(w * obj_ratio)
        return f'''
<div class="abs" style="left:{x - 40}px;top:{y - 40}px;width:{w + 80}px;height:{h + 80}px">
 <i class="brk tl" style="left:0;top:0"></i><i class="brk tr" style="right:0;top:0"></i><i class="brk bl" style="left:0;bottom:0"></i><i class="brk br" style="right:0;bottom:0"></i></div>
<img class="obj" src="{A['object']}" style="left:{x}px;top:{y}px;width:{w}px">'''
    tb = f'<div class="badge k tag" style="left:600px;top:1020px;font-size:34px">{mk(c["tag_bottom"])}</div>' if c.get('tag_bottom') else ''
    P['v3-34'] = frame(1080, 1440, f'''
<div class="beam c" style="left:-100px;top:980px;width:1500px;transform:rotate(-24deg);opacity:.75"></div>{obj(330, 330, 690)}
<div class="badge r tag" style="left:640px;top:250px;font-size:34px">{mk(c['tag_top'])}</div>
<img class="person" src="{pg}" style="left:-150px;bottom:-30px;width:1150px">
{tb}
{title(c['title_34'], 70, 90, 108, 950)}
{title(c.get('subtitle_34', []), 70, 215, 84, 600)}''', hud, c.get('hud_right', ''))
    P['v3-43'] = frame(1440, 1080, f'''
<div class="beam c" style="left:300px;top:900px;width:1400px;transform:rotate(-24deg);opacity:.75"></div>{obj(760, 300, 600)}
<div class="badge r tag" style="left:1100px;top:225px;font-size:32px">{mk(c['tag_top'])}</div>
<img class="person" src="{pg}" style="left:-120px;bottom:-30px;width:1060px">
{title(c['title_43'], 80, 90, 110, 1280)}''', hud, c.get('hud_right', ''))

    c = cfg['v4']
    tasks = '\n'.join(f'<div class="task{" on" if i == 0 else ""}"><div><span class="n">{i + 1:02d}</span>{mk(t)}</div></div>'
                      for i, t in enumerate(c['tasks']))
    P['v4-34'] = frame(1080, 1440, f'''
{title(c['title_34'], 70, 100, 104, 950)}
<div class="abs" style="left:70px;top:390px;width:640px">{tasks}</div>
<img class="person" src="{pa}" style="left:330px;bottom:-30px;width:900px">''', hud, c.get('hud_right', ''))
    P['v4-43'] = frame(1440, 1080, f'''
{title(c['title_43'], 80, 90, 100, 1280)}
<div class="abs" style="left:80px;top:330px;width:640px">{tasks}</div>
<img class="person" src="{pa}" style="left:700px;bottom:-30px;width:820px">''', hud, c.get('hud_right', ''))
    return P


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    render = '--render' in sys.argv
    only = None
    if '--only' in sys.argv:
        only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
        args = [a for a in args if a != sys.argv[sys.argv.index('--only') + 1]]
    cfg_path, out = os.path.abspath(args[0]), os.path.abspath(args[1])
    cfg = json.load(open(cfg_path)); base = os.path.dirname(cfg_path)
    os.makedirs(os.path.join(out, 'assets'), exist_ok=True)
    shutil.copy(os.path.join(HERE, 'cover.css'), out)
    if not os.path.isdir(os.path.join(out, 'fonts')):
        shutil.copytree(FONTS, os.path.join(out, 'fonts'))
    A = {}
    for k, p in cfg['assets'].items():
        src = p if os.path.isabs(p) else os.path.join(base, p)
        dst = os.path.join(out, 'assets', f'{k}{os.path.splitext(src)[1]}')
        shutil.copy(src, dst); A[k] = f'assets/{os.path.basename(dst)}'
    ow, oh = Image.open(os.path.join(out, A['object'])).size if 'object' in A else (1, 1)
    pages = build(cfg, A, oh / ow)
    for k, v in pages.items():
        if only and k.split('-')[0] not in only: continue
        open(os.path.join(out, f'{k}.html'), 'w').write(HEAD + v + FIT)
    print('pages:', ', '.join(sorted(k for k in pages if not only or k.split('-')[0] in only)))
    if not render: return
    name, labels = cfg.get('name', 'cover'), {**LABELS, **cfg.get('labels', {})}
    jpgs = {}
    for k in sorted(pages):
        if only and k.split('-')[0] not in only: continue
        r = subprocess.run([OPENEDIT, 'render', os.path.join(out, f'{k}.html'), '--stills', '0', '--out', os.path.join(out, f'out-{k}'), '--no-text-floor'],
                           capture_output=True, text=True)
        png = os.path.join(out, f'out-{k}', 'f000000-0.000s.png')
        if not os.path.exists(png): print('render failed', k, r.stderr[-400:]); continue
        v, ratio = k.split('-')
        dst = os.path.join(out, f'{v.upper()}-{labels[v]}-{"3比4" if ratio == "34" else "4比3"}.jpg')
        Image.open(png).convert('RGB').save(dst, quality=95); jpgs[k] = dst
    vs = sorted({k.split('-')[0] for k in jpgs})
    g = 12; o = Image.new('RGB', (len(vs) * (600 + g) + g, 600 + 450 + 3 * g), (40, 40, 40))
    for i, v in enumerate(vs):
        if f'{v}-34' in jpgs: o.paste(Image.open(jpgs[f'{v}-34']).resize((450, 600)), (g + i * (600 + g) + 75, g))
        if f'{v}-43' in jpgs: o.paste(Image.open(jpgs[f'{v}-43']).resize((600, 450)), (g + i * (600 + g), 600 + 2 * g))
    o.save(os.path.join(out, '总览.jpg'), quality=88)
    print('jpgs:', len(jpgs), '→', out)


if __name__ == '__main__':
    main()
