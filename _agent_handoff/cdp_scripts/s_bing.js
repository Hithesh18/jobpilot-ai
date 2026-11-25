const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_b_cfg.json'), 'utf8'));
  const outPath = path.join(L.HANDOFF_DIR, '_bing_out.json');
  const p = await L.getTab(browser, context, 'bing');
  const out = [];
  const log = [];
  for (const q of cfg.queries) {
    for (const first of (cfg.firsts || [1])) {
      const u = 'https://www.bing.com/search?setlang=en&q=' + encodeURIComponent(q) + '&filters=' + encodeURIComponent(cfg.filters || 'ex1:"ez2"') + '&first=' + first;
      try {
        await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await p.waitForTimeout(2000 + Math.random() * 1500);
        if (/captcha|challenge/i.test(p.url()) || await p.$('#b_captcha, iframe[src*=challenge], iframe[src*=turnstile]')) {
          log.push([q, first, 'CAPTCHA']);
          break;
        }
        const r = await p.evaluate(() => [...document.querySelectorAll('#b_results li.b_algo')].map(li => {
          const a = li.querySelector('h2 a');
          return a ? { t: a.innerText, u: a.href, s: li.innerText.replace(/\s+/g, ' ').slice(0, 300) } : null;
        }).filter(Boolean));
        r.forEach(x => out.push({ q, ...x }));
        log.push([q.slice(0, 70), first, r.length]);
        if (r.length < 5) break;
      } catch (e) {
        log.push([q.slice(0, 60), first, 'ERR ' + e.message.slice(0, 80)]);
      }
    }
  }
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
  return { log, n: out.length };
};
