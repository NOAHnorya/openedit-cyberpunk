#!/bin/zsh
# Person cut-out stickers for a cut: frames -> Vision masks -> remove static background flicker -> red outline webp.
# usage: cutout.sh <run-dir> [first-frame]      (run-dir holds <key>.mp4 and edl.json; first-frame > 1 processes only new frames, e.g. an appended CTA)
# env: CROP="2640:2160:560:0" SCALE="1056:864" COLOR=ff2e4d  (crop of the 4K cut around the person; frames at 30 fps)
set -e
RUN=${1:A}; FIRST=${2:-1}; T=${0:A:h}
KEY=${RUN:t}; CUT=$RUN/$KEY.mp4
CROP=${CROP:-2640:2160:560:0}; SCALE=${SCALE:-1056:864}; COLOR=${COLOR:-ff2e4d}
mkdir -p $RUN/seg/frames $RUN/seg/masks $RUN/seg/masks-clean $RUN/seg/sticker $RUN/seg/new
SS=$(python3 -c "print(($FIRST-1)/30)")
ffmpeg -v error -y -ss $SS -i $CUT -vf "fps=30,crop=$CROP,scale=$SCALE" -q:v 3 -start_number $FIRST $RUN/seg/new/f%05d.jpg
N=$(ls $RUN/seg/new | wc -l | tr -d ' '); echo "frames $N from f$FIRST"
rm -rf $RUN/seg/in && mkdir -p $RUN/seg/in
for f in $RUN/seg/new/*.jpg; do mv $f $RUN/seg/frames/; ln -sf $RUN/seg/frames/${f:t} $RUN/seg/in/; done
osascript -l JavaScript $T/segment_batch.js $RUN/seg/in $RUN/seg/masks 0
python3 - $RUN <<'PY'
import json, sys
run = sys.argv[1]; e = json.load(open(f'{run}/edl.json')); segs = []; t = 0.0
for r in e['ranges']:
    d = round((r['end'] - r['start']) * 30) / 30; a = int(round(t * 30)) + 1; t += d; segs.append([a, int(round(t * 30))])
json.dump(segs, open(f'{run}/seg/segs.json', 'w'))
PY
LAST=$(( FIRST + N - 1 ))
python3 $T/clean_masks.py $RUN/seg/frames $RUN/seg/masks $RUN/seg/masks-clean "$(cat $RUN/seg/segs.json)" $FIRST $LAST 2>&1 | grep -v -i nan
rm -f $RUN/seg/sticker/f$(printf %05d $(( FIRST - 1 ))).webp
COLOR=$COLOR python3 $T/outline_seq.py $RUN/seg/frames $RUN/seg/masks-clean $RUN/seg/sticker
echo "stickers $(ls $RUN/seg/sticker | wc -l | tr -d ' ')"
