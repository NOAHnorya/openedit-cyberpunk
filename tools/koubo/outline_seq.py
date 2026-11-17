# masks + frames -> RGBA webp stickers with red outline, temporally smoothed mask
import sys, os
from multiprocessing import Pool
from PIL import Image, ImageFilter, ImageChops
FR, MK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
C = os.environ.get('COLOR', 'ff2e4d'); COLOR = tuple(int(C[i:i + 2], 16) for i in (0, 2, 4))
names = sorted(n[:-4] for n in os.listdir(MK) if n.endswith('.png'))
def load(i):
    i = max(0, min(len(names) - 1, i)); return Image.open(f'{MK}/{names[i]}.png').convert('L')
def work(i):
    out = f'{OUT}/{names[i]}.webp'
    if os.path.exists(out): return
    a, b, c = load(i - 1), load(i), load(i + 1)
    m = Image.blend(Image.blend(a, c, 0.5), b, 0.5)           # .25/.5/.25 temporal smoothing
    m = m.filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: 255 if v > 150 else (0 if v < 90 else int((v - 90) * 255 / 60)))
    r = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MaxFilter(9))
    ring = r.filter(ImageFilter.GaussianBlur(4)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(1))
    fr = Image.open(f'{FR}/{names[i]}.jpg').convert('RGB')
    img = Image.new('RGBA', fr.size, COLOR + (0,))
    col = Image.new('RGBA', fr.size, COLOR + (255,)); col.putalpha(ring)
    img = Image.alpha_composite(img, col)
    p = fr.convert('RGBA'); p.putalpha(m)
    img = Image.alpha_composite(img, p)
    img.save(out, 'WEBP', quality=88, method=2)
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    with Pool(8) as pool: pool.map(work, range(len(names)), chunksize=32)
    print('stickers', len(os.listdir(OUT)))
