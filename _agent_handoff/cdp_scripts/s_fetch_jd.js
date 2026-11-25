// Fetch JD text for each URL in _ss_urls.json in ONE background tab -> ../_ss_jds.json {url: text}
const fs = require('fs');
const path = require('path');

module.exports = async (browser, context) => {
  const urls = JSON.parse(fs.readFileSync(path.join(__dirname, '_ss_urls.json'), 'utf8'));
  const s = await browser.newBrowserCDPSession();
  const waiter = context.waitForEvent('page', { timeout: 15000 });
  await s.send('Target.createTarget', { url: 'about:blank', background: true });
  const pg = await waiter;
  await s.detach().catch(() => {});
  const ps = await context.newCDPSession(pg);
  await ps.send('Emulation.setFocusEmulationEnabled', { enabled: true }).catch(() => {});
  const out = {};
  try {
    for (const u of urls) {
      if (/linkedin\.com/i.test(u)) {
        out[u] = { text: 'SKIPPED: never open LinkedIn in the logged-in Chrome - use li_jd.py (guest API)' };
        continue;
      }
      try {
        await pg.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await pg.waitForTimeout(4000 + Math.random() * 4000);
        const t = await pg.evaluate(() => {
          const secs = Array.from(document.querySelectorAll('[data-at*="section-text"], [data-at="job-ad-content"]')).map(e => e.innerText).join(' ');
          return secs.length > 400 ? secs : document.body.innerText;
        });
        out[u] = {
          text: t.replace(/\s+/g, ' ').slice(0, 15000),
          apply: await pg.evaluate(() => Array.from(document.querySelectorAll('a,button')).map(e => e.innerText.trim()).filter(x => /bewerb|apply/i.test(x)).slice(0, 3).join(' | '))
        };
      } catch (e) {
        out[u] = { text: 'ERR ' + e.message.slice(0, 100) };
      }
    }
  } finally {
    await pg.close().catch(() => {});
  }
  fs.writeFileSync(path.join(__dirname, '..', '_ss_jds.json'), JSON.stringify(out, null, 1));
  return 'fetched ' + Object.keys(out).length;
};
