#!/bin/zsh
# 合成样片：12 秒、不含真人、全程离线免费（不登录 VEED，不用 FAL_KEY）。可重复运行，每次重建 runs/demo/。
# usage: zsh examples/demo/make.sh              完整流程，产出 runs/demo/demo-final.mp4
#        zsh examples/demo/make.sh --stills     只做到静帧拼图 runs/demo/stills.jpg（改 scenes.json 后快速检查）
#        zsh examples/demo/make.sh --preview    完整流程，再把拼图缩成 docs/preview.jpg（README 用）
#        zsh examples/demo/make.sh --cover      只出封面：cover.json 的 4 种版式 × 3:4 / 4:3 -> runs/demo/cover/
# 需要：macOS（say）、ffmpeg、node、npm install 过的 openedit、带 Pillow + numpy 的 python3、
#       带 faster-whisper 的 Python（查找顺序见 AGENTS.md「转写」）且 small 模型已下载过一次（DOWNLOAD=1）。
#
# 每一步对应真实流程里的哪一步：
#   配音   macOS say 念台词 + 深色底       ← 真实片子是你的口播粗剪 runs/<key>/<key>.mp4
#   转写   tools/transcribe-local.sh       ← 一样
#   素材   ffmpeg 测试图案 + Pillow 界面    ← 真实片子是你的录屏、截图，放 runs/<key>/media/
#   贴纸   assets.py 画的半身剪影           ← 换成自己的素材后，用 tools/koubo/cutout.sh runs/<key> 生成真人贴纸
#   页面   templates/cyberpunk/build.py    ← 一样，配置是本目录的 scenes.json
set -euo pipefail
HERE=${0:A:h}; ROOT=${HERE:h:h}; RUN=$ROOT/runs/demo; OE=$ROOT/node_modules/.bin/openedit
DUR=12; FPS=30; FRAMES=$(( DUR * FPS ))
STILLS=0.2,2.2,3.6,5.6,6.9,8.6,9.5,11.4   # 标题虚影入场、卡片、案例+特写、大标签、清单点亮×2、故障揭晓、推近
mode=${1:-all}
cd $ROOT

PY=""
for c in ${DEMO_PY:-} $ROOT/.venv/bin/python python3; do
  [[ -n $c ]] && command -v $c >/dev/null && $c -c 'import PIL, numpy' 2>/dev/null && { PY=$c; break; }
done
[[ -n $PY ]] || { echo "需要带 Pillow 和 numpy 的 python3：pip3 install pillow numpy（或设 DEMO_PY）" >&2; exit 1; }
[[ -x $OE ]] || { echo "没有 $OE：先在仓库根目录 npm install" >&2; exit 1; }
step() { print -P "%F{cyan}== $*%f" }

mkdir -p $RUN/media $RUN/seg

# 1. 配音：优先 Tingting，其次系统里任意中文（大陆）声音，都没有就念英文版（时间点按 Tingting 调的，英文会对不齐）
step "1/9 配音 + 深色底 -> runs/demo/demo.mp4"
ZH="这是一套开源的口播剪辑模板。基于 OpenEdit，转写和抠像都在本地跑。案例、清单和卡片，写在一份配置里。零付费，克隆就能用。"
EN="An open source template for talking-head edits. Built on OpenEdit, transcription and cut-outs run locally. Cases, checklists and cards live in one config. Zero cost: clone it and go."
voice=""; lang=zh; text=$ZH
if say -v '?' | grep -q '^Tingting '; then voice=Tingting
else voice=$(say -v '?' | sed -nE 's/^(.*[^ ]) +zh_CN +#.*/\1/p' | head -1); fi
if [[ -z $voice ]]; then voice=Samantha; lang=en; text=$EN; fi
echo "voice: $voice ($lang)"
say -v $voice -r 200 -o $RUN/voice.aiff "$text"
# 提速 1.07 倍（不变调），前面留 0.2 秒，补齐到 12 秒
ffmpeg -v error -y -f lavfi -i "color=c=0x07090c:s=1080x1920:r=${FPS}" -i $RUN/voice.aiff \
  -filter_complex "[1:a]aresample=48000,atempo=1.07,adelay=200:all=1,apad[a]" -map 0:v -map "[a]" -t $DUR \
  -c:v libx264 -tune stillimage -pix_fmt yuv420p -c:a aac -b:a 192k $RUN/demo.mp4

# 2. 转写 + 修正听错的词 + 字幕
step "2/9 本地转写 -> transcript.json, captions.js"
$ROOT/tools/transcribe-local.sh $RUN/demo.mp4 --lang $lang --hint "OpenEdit" --force
[[ $lang == zh ]] && $PY $ROOT/tools/koubo/fix_transcript.py $RUN/transcript.json $HERE/fixes.json
$OE captions $RUN/transcript.json --out $RUN/captions.js

# 3. 案例素材：两段 5 秒「录屏」（ffmpeg 测试图案 + Pillow 画的窗口和标签；这台的 ffmpeg 没有 drawtext 也能跑）、一段放大特写、一张截图
step "3/9 案例素材 -> media/"
$PY $HERE/assets.py ui rec1 $RUN/media/rec1-ui.png
$PY $HERE/assets.py ui rec2 $RUN/media/rec2-ui.png
rec() {  # rec <out> <ffmpeg 图案源 1000x550> <界面 png>
  ffmpeg -v error -y -f lavfi -i "$2" -i $3 -f lavfi -i "color=c=0xff2e4d:s=1000x6:r=${FPS}" \
    -filter_complex "[0:v]pad=1000:590:0:40:color=0x0b0e13[bg];[bg][1:v]overlay=0:0[u];[u][2:v]overlay=x='-w+w*t/5':y=582:eof_action=pass[v]" \
    -map "[v]" -t 5 -r $FPS -c:v libx264 -pix_fmt yuv420p -crf 20 $1
}
rec $RUN/media/rec1.mp4 "mandelbrot=s=1000x550:rate=${FPS}:start_scale=2:end_scale=0.6,format=gbrp,hue=s=0,eq=contrast=1.3:brightness=-0.2,colorchannelmixer=rr=0.25:gg=0.85:bb=1.0" $RUN/media/rec1-ui.png
rec $RUN/media/rec2.mp4 "life=s=500x275:rate=${FPS}:ratio=0.1:mold=6:life_color=#2ef2ff:death_color=#0b0e13:mold_color=#2a0c16,scale=1000:550:flags=neighbor" $RUN/media/rec2-ui.png
# 放大特写：录屏左上的状态面板（真实片子里是演示手势那一小块）
ffmpeg -v error -y -i $RUN/media/rec1.mp4 -vf "crop=320:230:30:70,scale=640:460:flags=lanczos" -c:v libx264 -pix_fmt yuv420p -crf 18 $RUN/media/rec1-zoom.mp4
$PY $HERE/assets.py terminal $RUN/media/terminal.jpg

# 4. 人像贴纸：没有真人，用剪影代替。换成自己的素材后，用 tools/koubo/cutout.sh runs/<key> 生成真人贴纸
step "4/9 剪影贴纸 -> seg/sticker/ ($FRAMES 帧)"
$PY $HERE/assets.py sticker $RUN/seg/sticker $FRAMES

# 封面（--cover）：真实片子要从 4K 原片重新抠人像，见 koubo-edit skill 第 8 节；这里用同一个剪影
if [[ $mode == --cover ]]; then
  step "封面 -> cover/"
  $PY $HERE/assets.py cover $RUN/cover-src
  ffmpeg -v error -y -ss 2.5 -i $RUN/media/rec1.mp4 -frames:v 1 -q:v 3 $RUN/cover-src/compare-left.jpg
  cp $RUN/media/terminal.jpg $RUN/cover-src/compare-right.jpg
  $PY $ROOT/templates/cyberpunk/cover/build_covers.py $HERE/cover.json $RUN/cover --render
  echo "covers: $RUN/cover/总览.jpg"; exit 0
fi

# 5. 页面
step "5/9 scenes.json -> index.html"
cp $HERE/scenes.json $RUN/scenes.json
$OE safe-zone 9:16 --out $RUN
$PY $ROOT/templates/cyberpunk/build.py $RUN --refresh

# 6. 静帧拼图，逐张检查：字不压脸、卡片不重叠、字不溢出
step "6/9 静帧 -> stills.jpg"
rm -rf $RUN/stills
$OE render $RUN/index.html --out $RUN/stills --stills $STILLS --sheet $RUN/stills.jpg --no-text-floor
[[ $mode == --stills ]] && { echo "stills: $RUN/stills.jpg"; exit 0; }

# 7. 正式渲染（无声）
step "7/9 渲染 -> out.mp4"
$OE render $RUN/index.html --out $RUN/out.mp4 --fps $FPS --frames $FRAMES --no-text-floor

# 8. 配乐和卡点音效：没写 music，自动合成底乐
step "8/9 混音 -> audio/mix.m4a"
$PY $ROOT/templates/cyberpunk/mix.py $RUN --build

# 9. 合成成片
step "9/9 成片 -> demo-final.mp4"
$OE mux-audio --video $RUN/out.mp4 --audio $RUN/audio/mix.m4a --out $RUN/demo-final.mp4

# README 预览图：同一组静帧排成 4×2（render 的拼图是 3 列，8 张会空一格），宽 1600，小于 1 MB
if [[ $mode == --preview ]]; then
  $PY - $RUN/stills $ROOT/docs/preview.jpg <<'PY'
import os, sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
names = sorted(n for n in os.listdir(src) if n.endswith('.png'))
cols, gap, w = 4, 8, (1600 - 3 * 8) // 4                  # 4 columns of 394 px with 8 px gaps
h = round(w * 1920 / 1080); rows = -(-len(names) // cols)
im = Image.new('RGB', (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), (30, 32, 36))
for i, n in enumerate(names):
    im.paste(Image.open(f'{src}/{n}').convert('RGB').resize((w, h), Image.LANCZOS), ((i % cols) * (w + gap), (i // cols) * (h + gap)))
os.makedirs(os.path.dirname(out), exist_ok=True)
for q in (88, 80, 72, 64):
    im.save(sys.argv[2], quality=q, optimize=True, progressive=True)
    if os.path.getsize(sys.argv[2]) < 1024 * 1024: break
print('preview', im.size, os.path.getsize(sys.argv[2]) // 1024, 'KB ->', sys.argv[2])
PY
fi
echo "done: $RUN/demo-final.mp4"
