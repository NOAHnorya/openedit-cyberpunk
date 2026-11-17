#!/usr/bin/env python3
"""Check candidate cuts for a slip by splicing audio and re-transcribing it (the agent cannot listen).
usage: python3 tools/koubo/candidates.py <spec.json>
  re-runs itself with the faster-whisper Python, first found: $WHISPER_PY -> <repo>/.venv -> ~/OpenMontage/.venv
spec.json: {"sources": {"p92": "/path/PMR00092.MOV"},
            "candidates": {"drop 第二个就是": [["p92", 71.0, 71.85], ["p92", 74.03, 76.0]], ...},
            "prompt": "以下是普通话的句子。Agents.md。"}
Pick the candidate whose text has no repeated phrase and no missing word; if none is clean, keep the original."""
import json, sys, subprocess, wave, tempfile, os


def whisper_python():
    if os.environ.get('WHISPER_PY'): return os.environ['WHISPER_PY']
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tools/koubo -> repo root
    for p in (os.path.join(root, '.venv', 'bin', 'python'), os.path.expanduser('~/OpenMontage/.venv/bin/python')):
        if os.access(p, os.X_OK): return p


if not os.environ.get('KOUBO_WHISPER_PY_RUNNING'):
    py = whisper_python()
    if py:
        os.environ['KOUBO_WHISPER_PY_RUNNING'] = '1'
        os.execv(py, [py, '-I', os.path.abspath(__file__), *sys.argv[1:]])
try:
    from faster_whisper import WhisperModel
except ImportError:
    sys.exit('faster-whisper not found: set WHISPER_PY, or run: python3 -m venv .venv && .venv/bin/pip install faster-whisper')
spec = json.load(open(sys.argv[1])); SR = 16000; cache = {}
def pcm(src):
    if src not in cache:
        cache[src] = subprocess.run(['ffmpeg', '-v', 'error', '-i', spec['sources'][src], '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return cache[src]
m = WhisperModel('small', device='cpu', compute_type='int8')
for name, parts in spec['candidates'].items():
    data = b''.join(pcm(s)[int(a * SR) * 2:int(b * SR) * 2] for s, a, b in parts)
    f = tempfile.NamedTemporaryFile(suffix='.wav', delete=False); w = wave.open(f.name, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data); w.close()
    segs, _ = m.transcribe(f.name, language='zh', initial_prompt=spec.get('prompt', '以下是普通话的句子。'), vad_filter=False)
    print(f"{name}: {''.join(s.text for s in segs)}"); os.unlink(f.name)
