// Offline Web Audio renders of synth.html (cue sounds and the synthesized music bed) to 48 kHz stereo wav.
// usage:
//   node render.mjs <audio-dir> <seconds>          sfx/{glitch,pop,riser,impact}.wav, plus music/tech-{A,B}.wav when seconds > 0
//   node render.mjs --music <out.wav> <seconds> [A|B]   only the music bed (default variant A) into one file
import { launch } from './chrome.mjs';
import fs from 'fs';
import path from 'path';
const args = process.argv.slice(2);
const musicOnly = args[0] === '--music';
const [outPath, dur, variant = 'A'] = musicOnly ? args.slice(1) : args;
if (!outPath || (musicOnly && !(+dur > 0))) {
  console.error('usage: node render.mjs <audio-dir> <seconds>  |  node render.mjs --music <out.wav> <seconds> [A|B]');
  process.exit(2);
}
const b = await launch();
const p = await b.newPage();
await p.goto('file://' + new URL('./synth.html', import.meta.url).pathname);
function wav(file, int16bytes) { const h = Buffer.alloc(44); const n = int16bytes.length;
  h.write('RIFF', 0); h.writeUInt32LE(36 + n, 4); h.write('WAVEfmt ', 8); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22);
  h.writeUInt32LE(48000, 24); h.writeUInt32LE(48000 * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(n, 40);
  fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, Buffer.concat([h, int16bytes])); }
async function dump(file) { const len = await p.evaluate(() => window.__buf.length); await p.evaluate(() => measurePeak()); const parts = [];
  for (let s = 0; s < len; s += 48000 * 5) parts.push(Buffer.from(await p.evaluate(([a, n]) => chunk(a, n), [s, 48000 * 5]), 'base64'));
  wav(file, Buffer.concat(parts)); console.log('wrote', file, (len / 48000).toFixed(2) + 's'); }
async function music(v, file) { const t0 = Date.now(); await p.evaluate(([v, d]) => renderMusic(v, d), [v, +dur]); await dump(file);
  console.log('  render', ((Date.now() - t0) / 1000).toFixed(1) + 's'); }
if (musicOnly) await music(variant, outPath);
else {
  for (const k of ['glitch', 'pop', 'riser', 'impact']) { await p.evaluate(k => renderSfx(k), k); await dump(`${outPath}/sfx/${k}.wav`); }
  if (+dur > 0) for (const v of ['A', 'B']) await music(v, `${outPath}/music/tech-${v}.wav`);
}
await b.close();
