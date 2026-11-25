// Deep StepStone sweep (English filter fdl=en) in ONE background tab, paginating until empty.
const fs = require('fs');
const path = require('path');

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_ss_cfg.json'), 'utf8'));
  const s = await browser.newBrowserCDPSession();
  const waiter = context.waitForEvent('page', { timeout: 15000 });
  await s.send('Target.createTarget', { url: 'about:blank', background: true });
  const pg = await waiter;
  await s.detach().catch(() => {});
  const ps = await context.newCDPSession(pg);
  await ps.send('Emulation.setFocusEmulationEnabled', { enabled: true }).catch(() => {});
  const cards = {};
  const log = [];
  try {
    for (const q of cfg.queries) {
      for (let p = 1; p <= (cfg.maxPages || 10); p++) {
        const url = `https://www.stepstone.de/jobs/${q}${cfg.where ? '/in-' + cfg.where : ''}?${cfg.lang === 'any' ? '' : 'fdl=en&'}${cfg.age ? 'ag=' + cfg.age + '&' : ''}action=sort_publish&page=${p}`;
        await pg.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await pg.waitForTimeout(4000 + Math.random() * 4000);
        const got = await pg.evaluate(() => {
          const out = [];
          for (const a of document.querySelectorAll('article')) {
            const l = a.querySelector('a[href*="stellenangebote--"]');
            if (!l) continue;
            const lines = a.innerText.split('\n').map(x => x.trim()).filter(Boolean);
            const comp = a.querySelector('[data-at="job-item-company-name"]')?.innerText?.trim() || '';
            const loc = a.querySelector('[data-at="job-item-location"]')?.innerText?.trim() || '';
            const date = a.querySelector('time')?.getAttribute('datetime') || a.querySelector('time')?.innerText || '';
            out.push({ title: l.innerText.trim().split('\n')[0], company: comp || lines[1] || '', loc, date, url: l.href.split('?')[0] });
          }
          const total = (document.body.innerText.match(/(\d+)\s+Treffer/) || [])[1] || '';
          return { out, total };
        });
        let fresh = 0;
        for (const c of got.out) {
          if (!cards[c.url]) {
            cards[c.url] = { ...c, q, page: p };
            fresh++;
          }
        }
        log.push(`${q} p${p}: ${got.out.length} cards (${fresh} new) total=${got.total}`);
        if (got.out.length === 0 || (fresh === 0 && p > 1 && !cfg.noEarlyStop)) break;
      }
    }
  } finally {
    await pg.close().catch(() => {});
  }
  fs.writeFileSync(path.join(__dirname, '..', cfg.out || '_ss_cards.json'), JSON.stringify(Object.values(cards), null, 1));
  return log.join('\n') + `\nTOTAL unique cards: ${Object.keys(cards).length}`;
};
