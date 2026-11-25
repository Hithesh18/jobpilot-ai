const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_list_cfg.json'), 'utf8').replace(/^\uFEFF/, ''));
  const p = await L.getTab(browser, context, 'list');
  const jobs = {};
  const log = [];
  for (const u of cfg.urls) {
    try {
      await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(cfg.wait || 3500);
      const gate = await p.evaluate(() => {
        const txt = document.body ? document.body.innerText.slice(0, 700) : '';
        return /additional verification|cloudflare|verify you are human|unusual traffic/i.test(txt);
      });
      if (gate) {
        log.push([u.slice(-70), 'CLOUDFLARE_GATE']);
        break;
      }
      const r = await p.evaluate(() => [...document.querySelectorAll('.job_seen_beacon, .cardOutline, [data-jk]')].map(c => {
        const a = c.querySelector('a[data-jk]') || (c.matches('[data-jk]') ? c : null);
        const jk = a ? a.getAttribute('data-jk') : c.getAttribute('data-jk');
        if (!jk || /0123|1234|2345|3456|4567|5678|6789|789a|89ab|9abc|abcd|bcde|cdef|fedc|edcb|dcba|a1b2|b2c3|c3d4|d4e5|e5f6/i.test(jk)) return null;
        const titleEl = c.querySelector('h2.jobTitle span[title], h2.jobTitle, a[data-jk]');
        const co = c.querySelector('[data-testid="company-name"], .companyName');
        const loc = c.querySelector('[data-testid="text-location"], .companyLocation');
        const age = c.querySelector('[data-testid="myJobsStateDate"], .date');
        return {
          jk,
          title: titleEl ? titleEl.innerText.trim() : '',
          company: co ? co.innerText.trim() : '',
          loc: loc ? loc.innerText.trim() : '',
          age: age ? age.innerText.trim() : '',
          url: jk ? 'https://de.indeed.com/viewjob?jk=' + jk : '',
        };
      }).filter(x => x && x.jk && x.title));
      r.forEach(x => { if (!jobs[x.jk] || !jobs[x.jk].company) jobs[x.jk] = x; });
      log.push([u.slice(-70), r.length]);
    } catch (e) {
      log.push([u.slice(-70), 'ERR ' + e.message.slice(0, 100)]);
    }
  }
  fs.writeFileSync(path.join(L.HANDOFF_DIR, '_indeed_out.json'), JSON.stringify(jobs, null, 1));
  return { log, n: Object.keys(jobs).length };
};
