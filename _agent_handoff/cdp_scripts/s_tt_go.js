const fs = require('fs');
const path = require('path');
const L = require('./lib.js');

module.exports = async () => {
  const prof = L.loadCandidateProfile();
  const cand = prof.candidate || {};
  const firstName = cand.first_name || 'Alex';
  const lastName = cand.last_name || 'Morgan';

  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_submit_cfg.json'), 'utf8'));
  const p = global.__tabs[cfg.tab];
  const fn = await p.inputValue('#candidate_first_name');
  const ln = await p.inputValue('#candidate_last_name');
  if (fn !== firstName || ln !== lastName) return { err: 'name readback', fn, ln, expected: `${firstName} ${lastName}` };
  await p.evaluate(() => document.querySelector('input[type=submit][name=commit]').click());
  await p.waitForTimeout(12000);
  const cap = await p.$('iframe[src*="captcha"], iframe[src*="turnstile"]');
  try { await p.screenshot({ path: path.join(cfg.folder, 'confirmation.png'), timeout: 15000 }); } catch (e) {}
  const t = await p.evaluate(() => document.body.innerText);
  const errs = await p.evaluate(() => [...document.querySelectorAll('[class*=error], .text-red-500, [role=alert]')].map(e => e.innerText.trim()).filter(Boolean).slice(0, 10));
  return { url: p.url(), captcha: !!cap, errs, text: t.slice(0, 700) };
};
