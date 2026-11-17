#!/usr/bin/env python3
"""Fix misheard words in an openedit transcript.json and merge key phrases into single words.
usage: fix_transcript.py <transcript.json> <fixes.json> [--from SEC]
fixes.json: {"replace": [["regex", "replacement"], ...],   # applied on each cue's joined text, word timings kept
             "merge":   ["工作规范。", "20分钟", ...]}      # phrases to fuse into one word (for data-key-words)
--from SEC only touches cues starting at or after SEC (e.g. a newly appended CTA)."""
import json, re, sys
p, fx = sys.argv[1], json.load(open(sys.argv[2]))
t0 = float(sys.argv[sys.argv.index('--from') + 1]) if '--from' in sys.argv else -1
t = json.load(open(p))
def replace(words, pat, rep):
    guard = 0
    while guard < 50:
        guard += 1
        J = ''.join(w['text'] for w in words); idx = []
        for k, w in enumerate(words): idx += [k] * len(w['text'])
        found = None
        for m in re.finditer(pat, J):
            i, j = idx[m.start()], idx[m.end() - 1]
            if not (i == j and words[i]['text'][m.start() - sum(len(words[k]['text']) for k in range(i)):][:len(rep)] == rep and m.group(0) == rep):
                found = m; break
        if not found: return words
        a, b = found.start(), found.end(); i, j = idx[a], idx[b - 1]
        si = sum(len(words[k]['text']) for k in range(i)); sj = sum(len(words[k]['text']) for k in range(j))
        new = words[i]['text'][:a - si] + re.sub(pat, rep, found.group(0)) + words[j]['text'][b - sj:]
        if i == j and new == words[i]['text']: return words
        words[i] = {'text': new, 'timestamp': [words[i]['timestamp'][0], words[j]['timestamp'][1]]}
        del words[i + 1:j + 1]
    return words
def merge(words, phrase):
    i = 0
    while i < len(words):
        acc = ''; j = i
        while j < len(words) and len(acc) < len(phrase): acc += words[j]['text']; j += 1
        if acc == phrase and j - i > 1:
            words[i] = {'text': phrase, 'timestamp': [words[i]['timestamp'][0], words[j - 1]['timestamp'][1]]}; del words[i + 1:j]
        i += 1
    return words
for c in t['chunks']:
    if c['timestamp'][0] < t0: continue
    for pat, rep in fx.get('replace', []): c['words'] = replace(c['words'], pat, rep)
    for ph in fx.get('merge', []): c['words'] = merge(c['words'], ph)
    c['text'] = ' '.join(w['text'] for w in c['words'])
t['text'] = ' '.join(c['text'] for c in t['chunks'])
json.dump(t, open(p, 'w'), ensure_ascii=False)
for c in t['chunks']:
    for w in c['words']:
        if w['text'] in fx.get('merge', []): print(f"{w['text']}@{w['timestamp'][0]:.2f}")
