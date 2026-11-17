import sys
from PIL import Image, ImageFilter, ImageChops
# usage: sticker.py <frame.png> <mask.png> <out-rgba.png> <stroke_px_at_full>
fr = Image.open(sys.argv[1]).convert('RGB'); m = Image.open(sys.argv[2]).convert('L')
stroke = int(sys.argv[4])
color = tuple(int(sys.argv[5][i:i+2],16) for i in (0,2,4)) if len(sys.argv)>5 else (255,255,255)
m = m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 150 else (0 if v < 90 else int((v-90)*255/60)))
# crop to the subject's bounding box with margin
bb = m.point(lambda v: 255 if v > 128 else 0).getbbox()
pad = stroke * 3
box = (max(bb[0]-pad,0), max(bb[1]-pad,0), min(bb[2]+pad, fr.width), min(bb[3]+pad, fr.height))
fr, m = fr.crop(box), m.crop(box)
ring = m.filter(ImageFilter.MaxFilter(3))
r = m
step = 9
while step <= stroke*2+1:
    r = r.filter(ImageFilter.MaxFilter(9)); step += 8
ring = r.filter(ImageFilter.GaussianBlur(10)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(1.5))
out = Image.new('RGBA', fr.size, (255,255,255,0))
white = Image.new('RGBA', fr.size, color+(255,)); white.putalpha(ring)
out = Image.alpha_composite(out, white)
person = fr.convert('RGBA'); person.putalpha(m)
out = Image.alpha_composite(out, person)
out.save(sys.argv[3]); print(box, out.size)
