# Remove static background (fur, chair, wall knot) wrongly kept in the person mask.
# Camera is locked: per source segment, build a clean background plate of two small zones from frames
# where the mask leaves them empty; in every frame drop mask pixels in those zones that match the plate
# and are not stable body pixels.
import numpy as np, os, sys, json
from PIL import Image, ImageFilter
from multiprocessing import Pool
FR, MK, DST, SEGS = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])  # SEGS: [[first,last],...] 1-based frame numbers
ZONES = json.loads(os.environ['ZONES']) if 'ZONES' in os.environ else [(880, 560, 1056, 864), (300, 0, 760, 70)]  # x0,y0,x1,y1 in the 1056x864 frame; find them with a flicker heat map first
def load(n):
    return (np.asarray(Image.open(f'{FR}/f{n:05d}.jpg').filter(ImageFilter.GaussianBlur(1.2)), np.float32),
            np.asarray(Image.open(f'{MK}/f{n:05d}.png').convert('L'), np.float32))
def plates(a, b):
    idx = list(range(a, b + 1, max(1, (b - a) // 120)))
    out = []
    for (x0, y0, x1, y1) in ZONES:
        fs = []; ms = []
        for n in idx:
            f, m = load(n); fs.append(f[y0:y1, x0:x1]); ms.append(m[y0:y1, x0:x1])
        fs = np.stack(fs); ms = np.stack(ms) > 128
        occ = ms.mean(0)
        masked = np.where(ms[..., None], np.nan, fs)
        with np.errstate(all='ignore'): plate = np.nanmedian(masked, 0)
        plate = np.where(np.isnan(plate), np.median(fs, 0), plate)
        out.append((plate, occ))
    return out
PL = {}
def seg_of(n):
    for k, (a, b) in enumerate(SEGS):
        if a <= n <= b: return k
def work(args):
    n, k = args
    f, m = load(n); m = m.copy(); removed = 0
    for (x0, y0, x1, y1), (plate, occ) in zip(ZONES, PL[k]):
        d = np.abs(f[y0:y1, x0:x1] - plate).max(-1)
        d = np.asarray(Image.fromarray(np.clip(d, 0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(3)), np.float32)
        bg = (d < 24) & (occ < 0.6) & (m[y0:y1, x0:x1] > 40)
        if bg.any():
            bgi = Image.fromarray((bg * 255).astype(np.uint8))
            bgi = bgi.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))   # keep only solid patches (fur), drop specks on fingers
            bgi = bgi.filter(ImageFilter.MaxFilter(5))                                    # cover the patch's soft fringe
            bg = (np.asarray(bgi) > 0) & (occ < 0.6)
            removed += int(bg.sum()); sub = m[y0:y1, x0:x1]; sub[bg] = 0
            closed = np.asarray(Image.fromarray(sub.astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)), np.float32)
            m[y0:y1, x0:x1] = np.where(bg, np.minimum(closed, sub), np.maximum(sub, closed))   # fill pinholes, never re-grow the removed patch
    Image.fromarray(m.astype(np.uint8)).save(f'{DST}/f{n:05d}.png'); return removed
if __name__ == '__main__':
    os.makedirs(DST, exist_ok=True)
    lo, hi = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (SEGS[0][0], SEGS[-1][1])
    ks = sorted({seg_of(n) for n in range(lo, hi + 1)})
    for k in ks: PL[k] = plates(*SEGS[k])
    jobs = [(n, seg_of(n)) for n in range(lo, hi + 1)]
    import multiprocessing as mp
    with mp.get_context("fork").Pool(8) as p: r = p.map(work, jobs, chunksize=16)
    print('frames', len(r), 'with background removed', sum(1 for x in r if x))
