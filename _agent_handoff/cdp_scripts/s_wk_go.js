const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const prof = L.loadCandidateProfile();
  const cand = prof.candidate || {};
  const firstName = cand.first_name || 'Alex';
  const lastName = cand.last_name || 'Morgan';

  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_submit_cfg.json'), 'utf8'));
  const p = await L.getTab(browser, context, cfg.tab);
  const fn = await p.inputValue('#firstname');
  const ln = await p.inputValue('#lastname');
  if (fn !== firstName || ln !== lastName) return { err: 'name readback', fn, ln, expected: `${firstName} ${lastName}` };
  await p.locator('button[type=submit]:has-text("Submit application")').dispatchEvent('click');
  await p.waitForTimeout(10000);
  const cap = await p.$('iframe[src*="captcha"], iframe[src*="turnstile"], iframe[title*="challenge" i]');
  try { await p.screenshot({ path: path.join(cfg.folder, 'confirmation.png'), timeout: 15000 }); } catch (e) {}
  const t = await p.evaluate(() => document.body.innerText);
  return { url: p.url(), captcha: !!cap, text: t.slice(0, 900) };
};
