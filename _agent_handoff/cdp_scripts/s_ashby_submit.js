const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const prof = L.loadCandidateProfile();
  const cand = prof.candidate || {};
  const fullName = cand.full_name || 'Alex Morgan';
  const firstName = cand.first_name || 'Alex';

  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_submit_cfg.json'), 'utf8'));
  const p = await L.getTab(browser, context, cfg.tab);
  const nm = await p.inputValue('#_systemfield_name').catch(() => null);
  const fn = await p.inputValue('input[name="_systemfield_first_name"], input[id*="first" i]').catch(() => null);
  if (nm !== fullName && fn !== firstName) return { err: 'name readback', nm, fn, expected: fullName };
  await p.locator('button:has-text("Submit Application")').click();
  await p.waitForTimeout(9000);
  try { await p.screenshot({ path: path.join(cfg.folder, 'confirmation.png'), timeout: 15000 }); } catch (e) {}
  const t = await p.evaluate(() => document.body.innerText);
  return { url: p.url(), text: t.slice(0, 700) };
};
