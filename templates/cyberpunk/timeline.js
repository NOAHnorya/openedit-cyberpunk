// Cyberpunk talking-head template: everything on screen is drawn from the page time t (data-stateless).
const CFG = window.SCENES, FPS = CFG.fps || 30, NFR = CFG.frames;
const MODES = CFG.scenes;                                   // [t0, t1, 'case'|'kp']
const BOUNDS = MODES.map(m => m[0]).filter(t => t > 0);
const STK = Object.assign({ dir: 'seg/sticker', case: { left: -110, width: 900 }, kp: { left: 90, width: 900 } }, CFG.sticker || {});
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ease = x => 1 - Math.pow(1 - x, 3);
const parseRanges = s => s.split(',').map(r => r.split('-').map(Number));
const els = [...document.querySelectorAll('[data-ranges],[data-in]')].map(el => ({
  el, fx: el.dataset.fx || (el.dataset.in ? 'up' : 'none'),
  ranges: el.dataset.ranges ? parseRanges(el.dataset.ranges) : [[+el.dataset.in, 999]],
  gh: [...el.querySelectorAll(':scope > .gh')], cg: el.querySelector(':scope > .cardghost'), main: el.querySelector(':scope > .main') }));
const tasks = [...document.querySelectorAll('.task[data-on]')].map(el => ({ el, r: parseRanges(el.dataset.on) }));
const vids = [...document.querySelectorAll('video[data-at]')];
const kfs = [...document.querySelectorAll('[data-kf]')].map(el => ({ el, k: el.dataset.kf.split(';').map(r => r.split(',').map(Number)) }));
const stk = document.getElementById('stk'), g1 = document.getElementById('stkg1'), g2 = document.getElementById('stkg2');
const glitch = document.getElementById('glitch'), media = document.getElementById('media'), objn = document.getElementById('objn');
for (let i = 0; i < 4; i++) glitch.appendChild(document.createElement('i'));
const rnd = n => { const x = Math.sin(n * 91.7 + 13.1) * 43758.5453; return x - Math.floor(x); };
const frameSrc = f => `${STK.dir}/f${String(Math.max(1, Math.min(NFR, f))).padStart(5, '0')}.webp`;
async function setSrc(img, src) { if (img.getAttribute('src') !== src) { img.setAttribute('src', src); try { await img.decode(); } catch (e) {} } }

window.__seek = async (t) => {
  const mode = (MODES.find(m => t >= m[0] && t < m[1]) || MODES[MODES.length - 1])[2];
  for (const o of els) {
    const r = o.ranges.find(([a, b]) => t >= a && t < b);
    if (!r) { o.el.style.display = 'none'; continue; }
    o.el.style.display = '';
    const p = ease(clamp((t - r[0]) / 0.35)), out = clamp((t - (r[1] - 0.2)) / 0.2);
    if (o.fx === 'up') {
      o.el.style.opacity = p * (1 - out); o.el.style.transform = `translateY(${(1 - p) * 34}px)`;
      if (o.cg) { const q = clamp((t - r[0]) / 0.4); o.cg.style.opacity = q < 1 ? 0.45 * (1 - q) : 0; o.cg.style.transform = `translateY(${-(1 - q) * 46}px)`; }
    } else if (o.fx === 'pop') { o.el.style.opacity = p; o.el.style.transform = `scale(${0.9 + 0.1 * p})`; }
    else if (o.fx === 'ghost' || o.fx === 'glitch') {          // titles: red/cyan afterimages sliding in, for 0.45 s
      const q = clamp((t - r[0]) / 0.45), e = ease(q);
      if (o.main) { o.main.style.opacity = o.fx === 'glitch' && q < 1 ? (Math.floor(t * 30) % 2 ? 0.55 : 1) : Math.min(1, 0.2 + e); }
      o.gh.forEach((g, i) => { const s = i ? 1 : -1; g.style.opacity = q < 1 ? 0.7 * (1 - e) : 0; g.style.transform = `translateX(${s * (1 - e) * 38}px)`; });
      o.el.style.transform = o.fx === 'glitch' && q < 1 ? `translateX(${(rnd(Math.floor(t * 30)) - 0.5) * 24 * (1 - q)}px)` : '';
      if (o.cg) o.cg.style.opacity = 0;
    }
  }
  let n = 0;
  tasks.forEach((o, i) => { const on = o.r.some(([a, b]) => t >= a && t < b); o.el.classList.toggle('on', on); if (on) n = i + 1; });
  if (objn) objn.textContent = String(n).padStart(2, '0');
  for (const { el, k } of kfs) {
    let v = k[0];
    for (let i = 0; i < k.length - 1; i++) {
      const [a, s1, x1, y1] = k[i], [b, s2, x2, y2] = k[i + 1];
      if (t >= a && t < b) { const q = ease(clamp((t - a) / (b - a))); v = [t, s1 + (s2 - s1) * q, x1 + (x2 - x1) * q, y1 + (y2 - y1) * q]; break; }
      if (t >= b) v = k[i + 1];
    }
    el.style.transform = `translate(${v[2]}px,${v[3]}px) scale(${v[1]})`;
  }
  for (const v of vids) {
    const shown = !v.closest('[style*="display: none"]');
    const rate = +(v.dataset.rate || 1), d = isFinite(v.duration) ? v.duration : 10;
    v.currentTime = shown ? clamp((t - +v.dataset.at) * rate, 0, d - 0.04) : 0;
  }
  // person sticker + afterimages right after a scene change
  const f = Math.floor(t * FPS + 1e-6) + 1, pos = STK[mode] || STK.kp;
  Object.assign(stk.style, { left: pos.left + 'px', width: pos.width + 'px', bottom: '-20px', visibility: 'visible' });
  await setSrc(stk, frameSrc(f));
  const b = BOUNDS.find(x => t >= x && t < x + 0.4);
  for (const [g, lag, dx] of [[g1, 4, 16], [g2, 8, -16]]) {
    if (b === undefined) { g.style.visibility = 'hidden'; continue; }
    const q = (t - b) / 0.4;
    Object.assign(g.style, { left: (pos.left + dx * (1 - q)) + 'px', width: pos.width + 'px', bottom: '-20px', visibility: 'visible', opacity: 0.4 * (1 - q) });
    await setSrc(g, frameSrc(f - lag));
  }
  // glitch bars on scene changes
  const gb = BOUNDS.find(x => t >= x && t < x + 0.17), bars = glitch.children;
  for (let i = 0; i < bars.length; i++) {
    if (gb === undefined) { bars[i].style.display = 'none'; continue; }
    const s = Math.floor(t * 30) * 7 + i; bars[i].style.display = '';
    bars[i].style.setProperty('--y', `${Math.floor(rnd(s) * 1800)}px`);
    bars[i].style.setProperty('--h', `${6 + Math.floor(rnd(s + 1) * 40)}px`);
    bars[i].style.setProperty('--c', i % 2 ? '#2ef2ff' : '#ff2e4d');
  }
  media.style.transform = gb !== undefined ? `translateX(${(rnd(Math.floor(t * 30)) - 0.5) * 18}px)` : '';
};
