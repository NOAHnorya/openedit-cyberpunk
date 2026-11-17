#!/usr/bin/env python3
"""Pictures for the synthetic demo (no real person, no downloads), drawn with Pillow.
usage: assets.py ui <rec1|rec2> <out.png>        window chrome + side panel laid over an ffmpeg test pattern (1000x590)
       assets.py terminal <out.png>              the terminal screenshot used in the last scene (1992x1180, shown at 996 wide)
       assets.py sticker <out-dir> <frames>      person sticker sequence f00001.webp.. : a head-and-shoulders silhouette
                                                 with the #FF2E4D outline, bobbing slightly (1056x864, like cutout.sh)
       assets.py cover <out-dir>                 person.png + object.png for cover.json
The sticker stands in for a real cut-out. With your own footage, make the real one with tools/koubo/cutout.sh <run>."""
import math, os, shutil, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RED, CY, INK = (255, 46, 77), (46, 242, 255), (233, 237, 240)
MONO = '/System/Library/Fonts/Menlo.ttc'
CJK = next((p for p in ('/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/STHeiti Medium.ttc',
                        '/System/Library/Fonts/PingFang.ttc') if os.path.exists(p)), MONO)
font = lambda size, path=MONO: ImageFont.truetype(path, size)

UI = {   # what each fake screen recording shows next to its test pattern
    'rec1': ('rec_01 — tools/transcribe-local.sh', 'REC_01 // TRANSCRIBE',
             ['WHISPER  small · zh', 'hint     OpenEdit', 'device   cpu (local)', '[ok] transcript.json']),
    'rec2': ('rec_02 — tools/koubo/cutout.sh', 'REC_02 // CUTOUT',
             ['VISION   person seg', 'frames   30 fps', 'outline  #FF2E4D', '[ok] seg/sticker/']),
}


def ui(kind, out):
    """Transparent overlay: title bar, a side panel (the detail the red box and inset zoom in on), a progress track."""
    title, chip, lines = UI[kind]
    im = Image.new('RGBA', (1000, 590), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 999, 39], fill=(11, 14, 19, 255))
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse([18 + i * 24, 13, 32 + i * 24, 27], fill=c)
    d.text((500, 20), title, font=font(17), fill=(150, 160, 170), anchor='mm')
    d.rectangle([40, 80, 340, 290], fill=(5, 7, 10, 225), outline=CY + (255,), width=2)   # panel; page box ≈ x82 y512 w300 h210
    d.text((58, 96), 'STATUS', font=font(16), fill=CY + (255,))
    for i, s in enumerate(lines):
        d.text((58, 128 + i * 38), s, font=font(21), fill=(RED if s.startswith('[ok]') else INK) + (255,))
    d.rectangle([20, 548, 20 + 12 * len(chip) + 24, 572], fill=RED + (255,))
    d.text((32, 560), chip, font=font(17), fill=(255, 255, 255, 255), anchor='lm')
    d.rectangle([0, 580, 999, 589], fill=(11, 14, 19, 230))                               # track under the moving playhead
    im.save(out)


def terminal(out):
    W, H = 1992, 1180
    im = Image.new('RGB', (W, H), (8, 10, 14)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 72], fill=(18, 22, 29))
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        d.ellipse([32 + i * 44, 22, 60 + i * 44, 50], fill=c)
    d.text((W // 2, 36), 'zsh — openedit-cyberpunk', font=font(30), fill=(140, 150, 160), anchor='mm')
    f, y = font(40), 120
    rows = [('$ ', 'git clone github.com/NOAHnorya/openedit-cyberpunk', CY),
            ('$ ', 'zsh examples/demo/make.sh', CY), None,
            ('  voice    ', 'macOS say            ok', INK), ('  words    ', 'faster-whisper       ok', INK),
            ('  sticker  ', 'Pillow silhouette    ok', INK), ('  render   ', 'headless Chrome      ok', INK),
            ('  mix      ', 'synth bed + cues     ok', INK), None,
            ('→ ', 'runs/demo/demo-final.mp4', (228, 255, 26))]
    for r in rows:
        if r:
            a, b, col = r
            d.text((64, y), a, font=f, fill=(110, 120, 130)); d.text((64 + d.textlength(a, font=f), y), b, font=f, fill=col)
        y += 72
    y += 10
    d.rectangle([48, y, 1180, y + 210], outline=RED, width=5)                                # the push-in ends on this box (x24-590, y430-535 shown)
    d.text((90, y + 62), 'COST  $0.00', font=font(68), fill=RED, anchor='lm')
    d.text((90, y + 152), '不登录 · 无 API key', font=font(54, CJK), fill=INK, anchor='lm')
    d.text((1230, y + 196), '█', font=f, fill=CY, anchor='ls')
    im.save(out, quality=92)


def silhouette(S=2):
    """Head-and-shoulders mask at S x 1056x864, smoothed so head, neck and shoulders read as one shape."""
    W, H = 1056 * S, 864 * S
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    e = lambda cx, cy, rx, ry: d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
    e(528, 262, 112, 142)                                    # head: top at y120
    d.rectangle([474 * S, 360 * S, 582 * S, 540 * S], fill=255)   # neck
    d.rounded_rectangle([118 * S, 560 * S, 938 * S, 1000 * S], radius=220 * S, fill=255)   # shoulders and chest
    e(528, 540, 230, 56)                                     # trapezius slope into the neck
    m = m.filter(ImageFilter.GaussianBlur(18 * S)).point(lambda v: 255 if v > 120 else 0)
    return m.filter(ImageFilter.GaussianBlur(S)).resize((1056, 864), Image.LANCZOS)


def sticker_base():
    """One RGBA sticker: dark body with a cyan rim light and scan lines, red ring like outline_seq.py draws."""
    m = silhouette(); W, H = m.size
    grad = Image.linear_gradient('L').resize((W, H))                         # 0 at top -> 255 at bottom
    body = Image.merge('RGB', [grad.point(lambda v, a=a, b=b: int(a + (b - a) * v / 255)) for a, b in ((34, 9), (42, 12), (56, 18))])
    lines = Image.new('L', (W, H), 0); dl = ImageDraw.Draw(lines)
    for y in range(0, H, 6): dl.line([0, y, W, y], fill=40)
    body = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), body, lines)
    rim = ImageChops.subtract(m, ImageChops.offset(m, 14, 10)).filter(ImageFilter.GaussianBlur(3))   # light from the upper left
    body = Image.composite(Image.new('RGB', (W, H), CY), body, rim.point(lambda v: int(v * 0.55)))
    r = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MaxFilter(9))
    ring = r.filter(ImageFilter.GaussianBlur(4)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(1))
    img = Image.new('RGBA', (W, H), RED + (0,)); col = Image.new('RGBA', (W, H), RED + (255,)); col.putalpha(ring)
    img = Image.alpha_composite(img, col)
    p = body.convert('RGBA'); p.putalpha(m)
    return Image.alpha_composite(img, p)


def sticker(out, frames):
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        if n.endswith('.webp'): os.remove(os.path.join(out, n))
    base, made = sticker_base(), {}
    for i in range(frames):
        dy = round(6 * math.sin(2 * math.pi * i / 30 / 2.4))       # ±6 px every 2.4 s; the gap at the bottom stays below the stage
        dst = f'{out}/f{i + 1:05d}.webp'
        if dy in made: shutil.copyfile(made[dy], dst); continue
        im = Image.new('RGBA', base.size, (0, 0, 0, 0)); im.paste(base, (0, dy)); im.save(dst, 'WEBP', quality=88, method=4)
        made[dy] = dst
    print('stickers', frames, '->', out)


def cover(out):
    """Cover sources for cover.json: the silhouette as a still person (1.5x) and a neon 'video' object."""
    os.makedirs(out, exist_ok=True)
    b = sticker_base(); b.resize((b.width * 3 // 2, b.height * 3 // 2), Image.LANCZOS).save(f'{out}/person.png')
    W, H = 900, 1200; im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 40, W - 60, H - 40], radius=60, fill=(8, 10, 14, 235), outline=CY + (255,), width=14)
    d.polygon([(330, 420), (330, 780), (620, 600)], fill=RED + (255,))
    d.text((W // 2, 170), '9:16', font=font(110), fill=CY + (255,), anchor='mm')
    d.text((W // 2, 1010), 'REC ●', font=font(80), fill=RED + (255,), anchor='mm')
    glow = im.split()[3].filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.6))
    halo = Image.new('RGBA', (W, H), CY + (0,)); halo.putalpha(glow)
    Image.alpha_composite(halo, im).save(f'{out}/object.png')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'ui': ui(sys.argv[2], sys.argv[3])
    elif cmd == 'terminal': terminal(sys.argv[2])
    elif cmd == 'sticker': sticker(sys.argv[2], int(sys.argv[3]))
    elif cmd == 'cover': cover(sys.argv[2])
    else: sys.exit(__doc__)
