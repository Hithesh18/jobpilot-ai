// Resolve external apply link on an Arbeitsagentur / GermanTechJobs detail URL configured in `_urls.json`.
const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const urls = JSON.parse(fs.readFileSync(path.join(__dirname, '_urls.json'), 'utf8'));
  const targetUrl = urls[0];
  if (!targetUrl) return { err: 'Provide target URL in _urls.json' };
  const p = await L.getTab(browser, context, 'fetch', targetUrl);
  await p.waitForTimeout(3000);
  const href = await p.evaluate(() => {
    const a = [...document.querySelectorAll('a')].find(el => /Externe Seite|Apply|Bewerben/i.test(el.innerText || ''));
    return a ? a.href : null;
  });
  if (!href) return { url: p.url(), note: 'no external link' };
  await p.goto(href, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await p.waitForTimeout(4000);
  return { url: p.url(), text: (await p.evaluate(() => document.body.innerText)).replace(/\n\s*\n+/g, '\n').slice(0, 5000) };
};
