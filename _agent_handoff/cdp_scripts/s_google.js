const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_g_cfg.json'), 'utf8'));
  const outPath = path.join(L.HANDOFF_DIR, '_google_out.json');
  const p = await L.getTab(browser, context, 'google');
  const out = [];
  const log = [];
  for (const q of cfg.queries) {
    for (const start of (cfg.starts || [0])) {
      const u = 'https://www.google.com/search?hl=en&q=' + encodeURIComponent(q) + '&tbs=' + (cfg.tbs || 'qdr:w2') + '&start=' + start;
      try {
        await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await p.waitForTimeout(8000 + Math.random() * 7000);
        if (/sorry|captcha/i.test(p.url()) || await p.$('#captcha-form, iframe[src*=recaptcha]')) {
          log.push([q, start, 'CAPTCHA']);
          fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
          return { log, n: out.length, captcha: true };
        }
        const r = await p.evaluate(() => [...document.querySelectorAll('a h3')].map(h => {
          const a = h.closest('a');
          const box = a.closest('div.g, div[data-hveid], div.MjjYud');
          return { t: h.innerText, u: a.href, s: box ? box.innerText.replace(/\s+/g, ' ').slice(0, 300) : '' };
        }));
        r.forEach(x => out.push({ q, ...x }));
        log.push([q.slice(0, 60), start, r.length]);
        if (r.length < 5) break;
      } catch (e) {
        log.push([q.slice(0, 60), start, 'ERR ' + e.message.slice(0, 80)]);
      }
    }
  }
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
  return { log, n: out.length };
};
