const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const urls = JSON.parse(fs.readFileSync(path.join(__dirname, '_urls.json'), 'utf8'));
  const p = await L.getTab(browser, context, 'tal');
  const out = [];
  for (const u of urls) {
    await p.goto(u, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(3000);
    const title = (await p.evaluate(() => document.body.innerText)).slice(80, 200).replace(/\n/g, ' | ');
    const b = p.locator('a:has-text("Bewerben"), button:has-text("Bewerben"), a:has-text("Apply")').first();
    const href = await b.getAttribute('href').catch(() => null);
    const pop = context.waitForEvent('page', { timeout: 12000 }).catch(() => null);
    await b.dispatchEvent('click').catch(() => {});
    const np = await pop;
    let fin = null;
    if (np) {
      await np.waitForLoadState('domcontentloaded').catch(() => {});
      await np.waitForTimeout(6000);
      fin = np.url();
      await np.close();
    } else {
      await p.waitForTimeout(5000);
      fin = p.url();
    }
    out.push({ title, href, fin });
  }
  return out;
};
