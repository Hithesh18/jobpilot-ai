const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const urls = JSON.parse(fs.readFileSync(path.join(__dirname, '_urls.json'), 'utf8'));
  const p = await L.getTab(browser, context, 'fetch');
  const out = {};
  for (const u of urls) {
    if (/linkedin\.com/i.test(u)) {
      out[u] = { err: 'SKIPPED_LINKEDIN_USE_GUEST_API' };
      continue;
    }
    try {
      await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(3500);
      out[u] = {
        final: p.url(),
        text: (await p.evaluate(() => document.body.innerText)).replace(/\n\s*\n+/g, '\n').slice(0, 9000)
      };
    } catch (e) {
      out[u] = { err: e.message.slice(0, 200) };
    }
  }
  fs.writeFileSync(path.join(L.HANDOFF_DIR, '_fetched.json'), JSON.stringify(out, null, 1));
  return Object.entries(out).map(([k, v]) => [k.slice(0, 90), v.final ? v.final.slice(0, 120) : v.err, v.text ? v.text.length : 0]);
};
