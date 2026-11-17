// Shared by render.mjs and balance.mjs: playwright-core from this repo's node_modules + the Chrome openedit installed.
// Chrome: $OPENEDIT_CHROME if set, otherwise the newest
//   <openedit state dir>/browser/chrome-headless-shell-<version>/chrome-headless-shell-mac-*/chrome-headless-shell
// where the state dir is $OPENEDIT_STATE_DIR or ~/Library/Application Support/veed-openedit (run `openedit install-browser` once).
import { chromium } from '../../../node_modules/playwright-core/index.mjs';
import fs from 'fs';
import os from 'os';
import path from 'path';

export function findChrome() {
  if (process.env.OPENEDIT_CHROME) return process.env.OPENEDIT_CHROME;
  const state = process.env.OPENEDIT_STATE_DIR || path.join(os.homedir(), 'Library', 'Application Support', 'veed-openedit');
  const root = path.join(state, 'browser');
  const ver = d => d.slice('chrome-headless-shell-'.length).split('.').map(Number);
  const newer = (a, b) => { const x = ver(a), y = ver(b); for (let i = 0; i < Math.max(x.length, y.length); i++) if ((x[i] || 0) !== (y[i] || 0)) return (y[i] || 0) - (x[i] || 0); return 0; };
  const dirs = fs.existsSync(root) ? fs.readdirSync(root).filter(d => /^chrome-headless-shell-\d+(\.\d+)*$/.test(d)).sort(newer) : [];
  for (const d of dirs) {
    for (const sub of fs.readdirSync(path.join(root, d)).filter(s => s.startsWith('chrome-headless-shell-mac-'))) {
      const exe = path.join(root, d, sub, 'chrome-headless-shell');
      if (fs.existsSync(exe)) return exe;
    }
  }
  throw new Error(`chrome-headless-shell not found under ${root}: run \`npx openedit install-browser\` or set OPENEDIT_CHROME`);
}

export function launch() {
  return chromium.launch({ executablePath: findChrome(), headless: true });
}
