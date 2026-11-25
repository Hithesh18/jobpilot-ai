const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const p = await L.getTab(browser, context, 'jv_sweep');
  const listUrls = [
    'https://www.jobvector.de/jobs/junior-software-developer/',
    'https://www.jobvector.de/jobs/full-stack-developer/',
    'https://www.jobvector.de/jobs/frontend-developer/',
    'https://www.jobvector.de/jobs/web-developer/',
    'https://www.jobvector.de/jobs/software-developer/',
    'https://www.jobvector.de/jobs/artificial-intelligence/'
  ];
  const byHref = new Map();
  for (const u of listUrls) {
    try {
      await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await p.waitForTimeout(3200);
      for (let s = 0; s < 3; s++) {
        await p.evaluate(() => window.scrollBy(0, 2200));
        await p.waitForTimeout(600);
      }
      const cards = await p.evaluate(() => {
        const out = [];
        for (const a of document.querySelectorAll('a[href*="/job/"]')) {
          const href = a.href.split('?')[0].split('#')[0];
          const card = a.closest('article, li, [class*="job"], [class*="card"]') || a.parentElement;
          const title = (a.innerText || '').trim().replace(/\s+/g, ' ');
          const text = (card ? card.innerText : title).trim().replace(/\s+/g, ' ').slice(0, 320);
          if (title.length > 3) out.push({ href, title, text });
        }
        return out;
      });
      for (const c of cards) {
        if (!byHref.has(c.href)) byHref.set(c.href, c);
      }
    } catch (e) {}
  }

  const allCards = [...byHref.values()];
  fs.writeFileSync(path.join(L.HANDOFF_DIR, '_jobvector_out.json'), JSON.stringify(allCards, null, 2));
  await L.closeTab('jv_sweep');
  return { count: allCards.length, sample: allCards.slice(0, 12) };
};
