#!/bin/zsh
# Local, free transcription for open-edit: faster-whisper -> `openedit whisper` -> runs/<key>/transcript.json.
# usage: tools/transcribe-local.sh <video> [--lang zh|en|...] [--model small|medium|large-v3] [--hint 'Claude Code, OpenEdit'] [--force]
#   --hint: names/terms said in the clip, spelled as they should appear (fixes misheard and split English words)
# Python with faster-whisper, first found: $WHISPER_PY -> <repo>/.venv -> ~/OpenMontage/.venv
#   (create one with ./setup.sh, which picks a Python 3.9-3.14: onnxruntime has no 3.15 wheels yet)
# Runs offline by default. The first run of a model downloads it once from Hugging Face:
#   set DOWNLOAD=1 for that run (behind a proxy, also set HTTPS_PROXY).
set -euo pipefail
here=${0:A:h}
ws=${here:h}
py=""
if [[ -n ${WHISPER_PY:-} ]]; then
  [[ -x $WHISPER_PY ]] || { echo "WHISPER_PY=$WHISPER_PY is not executable" >&2; exit 1; }
  py=$WHISPER_PY
else
  for c in $ws/.venv/bin/python $HOME/OpenMontage/.venv/bin/python; do
    [[ -x $c ]] && { py=$c; break; }
  done
fi
[[ -n $py ]] || { echo "no Python with faster-whisper: set WHISPER_PY, or run $ws/setup.sh (it builds .venv with a Python 3.9-3.14)" >&2; exit 1; }

media=$1; shift
lang=""; model=small; hint=""; force=()
while (( $# )); do
  case $1 in
    --lang) lang=$2; shift 2 ;;
    --model) model=$2; shift 2 ;;
    --hint) hint=$2; shift 2 ;;
    --force) force=(--force); shift ;;
    *) echo "unknown flag $1" >&2; exit 2 ;;
  esac
done

key=${${media:t}:r}
raw=$ws/runs/$key/fw-$model.json
mkdir -p ${raw:h}
[[ ${DOWNLOAD:-0} == 1 ]] || export HF_HUB_OFFLINE=1
langargs=(); [[ -n $lang ]] && langargs=(--lang $lang)
$py -I $here/fw_transcribe.py $media $raw --model $model $langargs --hint "$hint"
$ws/node_modules/.bin/openedit whisper $raw $media $force
