#!/usr/bin/env python3
"""Soundtrack for the cyberpunk template: music bed + cue sounds placed from scenes.json.
usage: mix.py <run-dir> [--music <file>] [--build]     (--build also runs openedit mix-audio -> audio/mix.m4a)
music bed: --music <file> (relative to the current dir) -> scenes.json "music" (relative to the run dir) -> otherwise a
synthesized bed (tools/koubo/webaudio, variant A, as long as the cut) written to <run>/audio/music-synth.wav.
glitch on every scene change; pop when a card / task / inset / pop-tag / highlight box appears and when a task turns on;
riser + impact on each time in scenes.json "hits". Short cues get a hand-set gainDb (mix-audio over-boosts sub-0.4 s sounds)."""
import json, sys, os, subprocess, shutil
import numpy as np
T = os.path.dirname(os.path.abspath(__file__)); run = os.path.abspath(sys.argv[1]); S = json.load(open(f'{run}/scenes.json'))
ROOT = os.path.dirname(os.path.dirname(T))   # templates/cyberpunk -> repo root
OE = os.path.join(ROOT, 'node_modules', '.bin', 'openedit')
cut = f'{run}/{S.get("cut", os.path.basename(run) + ".mp4")}'
if '--music' in sys.argv: music = os.path.abspath(sys.argv[sys.argv.index('--music') + 1])
elif S.get('music'): music = os.path.join(run, S['music'])   # absolute paths pass through join unchanged
else: music = None
os.makedirs(f'{run}/audio/sfx', exist_ok=True)
for f in ('glitch', 'pop', 'riser', 'impact'): shutil.copy(f'{T}/audio/{f}.wav', f'{run}/audio/sfx/{f}.wav')
voice = f'{run}/audio/voice-full.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', cut, '-vn', '-ac', '1', '-ar', '48000', voice], check=True)
def lufs(p, ss=None, t=None):
    cmd = ['ffmpeg', '-hide_banner'] + (['-ss', str(ss)] if ss else []) + ['-i', p] + (['-t', str(t)] if t else []) + ['-af', 'ebur128=framelog=quiet', '-f', 'null', '-']
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith('I:')][-1].split()[1])
def pcm(p): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', '48000', '-f', 's16le', '-'], capture_output=True).stdout, '<i2').astype(float) / 32768
v = pcm(voice); pk = np.array([np.abs(v[i:i + 4800]).max() for i in range(0, len(v) - 4800, 4800)]); pkdb = 20 * np.log10(pk + 1e-9)
p75 = float(np.percentile(pkdb[pkdb > -60], 75)); popdb = 20 * np.log10(np.abs(pcm(f'{T}/audio/pop.wav')).max())
VL = lufs(voice); dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', cut], capture_output=True, text=True).stdout)
if music is None:
    music = f'{run}/audio/music-synth.wav'
    subprocess.run(['node', os.path.join(ROOT, 'tools', 'koubo', 'webaudio', 'render.mjs'), '--music', music, str(round(dur + 1, 1)), 'A'], check=True)
if not os.path.isfile(music): sys.exit(f'music not found: {music}')
first = lambda o: float((o.get('ranges') or str(o.get('t0', 0))).split(',')[0].split('-')[0])
hits = S.get('hits', [])
pops = set()
for c in S.get('cards', []): pops.add(first(c))
tk = S.get('tasks')
if tk:
    for i, it in enumerate(tk['items']): pops.add(round(tk['appear'] + i * 0.2, 2)); pops.add(float(it['on'].split('-')[0]))
for sc in S['scenes']:
    c = sc.get('case') or {}
    for n in c.get('insets', []): pops.add(first(n))
    for g in c.get('tags', []):
        if g.get('pop'): pops.add(first(g))
    for b in c.get('inner_boxes', []): pops.add(first(b))
    for b in c.get('boxes', []):
        if b.get('fx') == 'pop': pops.add(first(b))
pops |= set(S.get('pops', []))
pops = sorted(p for p in pops if all(abs(p - h) > 0.15 for h in hits) and p < dur)
starts = [0.0] + [sc['t0'] for sc in S['scenes'] if 0 < sc['t0'] < dur]
tracks = [{"path": "audio/voice-full.wav", "atSec": 0, "role": "voice"},
          {"path": music, "atSec": 0, "gainDb": round(VL - 9 - lufs(music, 5, 40), 1), "role": "music", "fadeInSec": 0.5, "fadeOutSec": 2.5}]
tracks += [{"path": "audio/sfx/glitch.wav", "atSec": round(t + 0.02, 2), "gainDb": round(VL - 8.2, 1), "role": "sfx"} for t in starts]
tracks += [{"path": "audio/sfx/pop.wav", "atSec": t, "gainDb": round(p75 - 4 - popdb, 1), "role": "sfx"} for t in pops]
tracks += [{"path": "audio/sfx/riser.wav", "atSec": round(h - 1.25, 2), "role": "sfx"} for h in hits]
tracks += [{"path": "audio/sfx/impact.wav", "atSec": h, "role": "sfx"} for h in hits]
json.dump({"durationSec": round(dur, 3), "tracks": tracks}, open(f'{run}/audio/mix.json', 'w'), ensure_ascii=False, indent=1)
print(f'voice {VL} LUFS; {len(starts)} glitches, {len(pops)} pops, {len(hits)} hits -> {run}/audio/mix.json')
if '--build' in sys.argv:
    subprocess.run([OE, 'mix-audio', run, '--spec', 'audio/mix.json', '--out', 'audio/mix.m4a'], check=True)
