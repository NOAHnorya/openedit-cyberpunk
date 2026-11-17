"""Local transcription for open-edit with faster-whisper.

Run with a Python that has faster-whisper (transcribe-local.sh finds one). Writes Whisper-family JSON
({segments:[{start,end,text,words:[{word,start,end}]}]}) that `openedit whisper` maps.
"""
import argparse
import json
import re
import sys

from faster_whisper import WhisperModel

# Whisper drifts into Traditional characters on Mandarin; a Simplified prompt steers it back.
PROMPTS = {"zh": "以下是普通话的句子，使用简体中文。"}

ap = argparse.ArgumentParser()
ap.add_argument("media")
ap.add_argument("out")
ap.add_argument("--model", default="small")
ap.add_argument("--lang", default=None, help="ISO 639-1 code, e.g. zh / en; omit to auto-detect")
ap.add_argument("--hint", default="", help="terms said in the clip, spelled as they should appear, e.g. 'Claude Code, OpenEdit'")
a = ap.parse_args()

prompt = PROMPTS.get(a.lang or "", "")
if a.hint:
    prompt = f"{prompt}{'专有名词' if (a.lang or '').startswith('zh') else 'Terms'}：{a.hint}。"

model = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, info = model.transcribe(
    a.media,
    language=a.lang,
    word_timestamps=True,
    vad_filter=True,
    initial_prompt=prompt or None,
    hotwords=a.hint or None,
)
CJK = r"[㐀-鿿豈-﫿]"
FULL = {",": "，", "?": "？", "!": "！", ":": "：", ";": "；"}


def fix(text: str) -> str:
    """For Chinese, half-width punctuation right after a Chinese character becomes full-width."""
    if not (a.lang or "").startswith("zh"):
        return text
    return re.sub(rf"(?<={CJK})([,?!:;])", lambda m: FULL[m.group(1)], text)


def join_pieces(words):
    """In zh/ja mode Whisper splits English into sub-word pieces (' Cla' 'ude'); a piece with no
    leading space that continues a Latin piece belongs to the same word."""
    merged = []
    for w in words:
        prev = merged[-1] if merged else None
        if prev and re.match(r"[A-Za-z0-9]", w["word"]) and re.search(r"[A-Za-z0-9]$", prev["word"]):
            prev["word"] += w["word"]
            prev["end"] = w["end"]
        else:
            merged.append(dict(w))
    return merged


out = []
for s in segs:
    words = [{"word": fix(w.word), "start": round(w.start, 3), "end": round(w.end, 3)} for w in (s.words or [])]
    out.append({
        "start": round(s.start, 3),
        "end": round(s.end, 3),
        "text": fix(s.text.strip()),
        "words": join_pieces(words),
    })
with open(a.out, "w", encoding="utf-8") as f:
    json.dump({"language": info.language, "segments": out}, f, ensure_ascii=False, indent=1)
print(f"[fw_transcribe] {info.language}, {sum(len(s['words']) for s in out)} words -> {a.out}", file=sys.stderr)
