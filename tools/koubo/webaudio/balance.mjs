// Energy per frequency band of synth.html's music variants A and B (checks the bed stays low-mid, under the voice).
// usage: node balance.mjs
import { launch } from './chrome.mjs';
const b = await launch(); const p = await b.newPage();
await p.goto('file://' + new URL('./synth.html', import.meta.url).pathname);
for (const v of ['A', 'B']) {
  const r = await p.evaluate(async (v) => { await renderMusic(v, 25); const x = window.__buf.getChannelData(0).slice(48000 * 5);
    const N = 1 << 20, re = new Float64Array(N); for (let i = 0; i < Math.min(N, x.length); i++) re[i] = x[i] * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / N));
    // energy per band via Goertzel-free approach: use an OfflineAudioContext bank of bandpass filters
    const bands = [[20, 80], [80, 250], [250, 1000], [1000, 2500], [2500, 12000]], out = [];
    for (const [lo, hi] of bands) { const c = new OfflineAudioContext(1, x.length, 48000); const bf = c.createBuffer(1, x.length, 48000); bf.copyToChannel(x, 0);
      const s = c.createBufferSource(); s.buffer = bf; const h = c.createBiquadFilter(); h.type = 'highpass'; h.frequency.value = lo; const l = c.createBiquadFilter(); l.type = 'lowpass'; l.frequency.value = hi;
      const h2 = c.createBiquadFilter(); h2.type = 'highpass'; h2.frequency.value = lo; const l2 = c.createBiquadFilter(); l2.type = 'lowpass'; l2.frequency.value = hi;
      s.connect(h).connect(h2).connect(l).connect(l2).connect(c.destination); s.start(); const y = (await c.startRendering()).getChannelData(0); let e = 0; for (const q of y) e += q * q; out.push(e); }
    const tot = out.reduce((a, b) => a + b); return out.map(e => (100 * e / tot).toFixed(0) + '%').join(' '); }, v);
  console.log(v, '20-80 | 80-250 | 250-1k | 1k-2.5k | 2.5k+ :', r);
}
await b.close();
