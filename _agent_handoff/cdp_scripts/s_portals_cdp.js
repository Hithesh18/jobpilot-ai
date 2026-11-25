const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const cfgPath = path.join(L.HANDOFF_DIR, '_portals_cdp_cfg.json');
  const outPath = path.join(L.HANDOFF_DIR, '_portals_cdp_out.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8').replace(/^\uFEFF/, ''));
  const p = await L.getTab(browser, context, 'harvester_bg');
  const results = {};
  const summary = {};

  for (const [portal, spec] of Object.entries(cfg.portals || {})) {
    const urls = Array.isArray(spec) ? spec : (spec.urls || []);
    const linkRe = (!Array.isArray(spec) && spec.re)
      ? spec.re
      : '(stellenangebote--|/job/|/jobs/|/rc/clk|viewjob|/jobs/view|jobdetail|/stellenangebot|/details|/job-|/stelle/|/jobposting|/position|join\\.com/companies/|wearedevelopers\\.com/en/jobs/|englishjobs\\.de/jobs/|get-in-it\\.de/jobsuche/p|view\\?id=)';
    const scrolls = (!Array.isArray(spec) && spec.scroll) ? spec.scroll : 2;
    const byHref = new Map();

    for (const u of urls) {
      try {
        await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 28000 });
        await p.waitForTimeout(5000 + Math.random() * 4000);
        const bodyHead = await p.evaluate(() => (document.body ? document.body.innerText.slice(0, 700) : ''));
        if (/verify you are human|additional verification Required|unusual traffic|captcha/i.test(bodyHead)) {
          summary[portal] = (summary[portal] || 0);
          break;
        }
        for (let s = 0; s < scrolls; s++) {
          await p.evaluate(() => window.scrollBy(0, 2600));
          await p.waitForTimeout(900 + Math.random() * 900);
        }
        const items = await p.evaluate((reSrc) => {
          const re = new RegExp(reSrc, 'i');
          const out = [];
          if (location.hostname.includes('englishjobs.de')) {
            for (const c of document.querySelectorAll('div.js-job')) {
              const a = c.querySelector('a.js-joblink');
              const li = [...c.querySelectorAll('li')].map(x => x.innerText.trim());
              if (a && a.href) {
                out.push({
                  href: a.href.split('#')[0],
                  title: (c.querySelector('h3') || a).innerText.trim(),
                  company: li[0] || '',
                  location: li[1] || '',
                  text: ((c.querySelector('h3') || a).innerText + ' | ' + li.join(' | ')).replace(/\s+/g, ' ').trim().slice(0, 220),
                });
              }
            }
            if (out.length) return out;
          }
          if (location.hostname.includes('indeed.com')) {
            for (const c of document.querySelectorAll('.job_seen_beacon, .cardOutline, [data-jk]')) {
              const a = c.querySelector('a[data-jk]') || (c.matches('[data-jk]') ? c : null);
              const jk = a ? a.getAttribute('data-jk') : c.getAttribute('data-jk');
              if (!jk) continue;
              // Skip sequential hex decoy/honeypot cards
              if (/0123|1234|2345|3456|4567|5678|6789|789a|89ab|9abc|abcd|bcde|cdef|fedc|edcb|dcba|a1b2|b2c3|c3d4|d4e5|e5f6/i.test(jk)) continue;
              const titleEl = c.querySelector('h2.jobTitle span[title], h2.jobTitle, a[data-jk]');
              const co = c.querySelector('[data-testid="company-name"], .companyName');
              const loc = c.querySelector('[data-testid="text-location"], .companyLocation');
              const t = titleEl ? titleEl.innerText.trim() : '';
              const comp = co ? co.innerText.trim() : '';
              const l = loc ? loc.innerText.trim() : '';
              out.push({
                href: 'https://de.indeed.com/viewjob?jk=' + jk,
                title: t,
                company: comp,
                location: l,
                text: `${t} | ${comp} | ${l}`.slice(0, 220),
              });
            }
            if (out.length) return out;
          }
          for (const a of document.querySelectorAll('a[href]')) {
            const href = (a.href || '').split('#')[0];
            if (!href || !re.test(href)) continue;
            const card = a.closest('article, li, [data-at="job-item"], [class*="job"], [class*="Job"], [class*="card"], [class*="Card"]') || a.parentElement;
            const title = (a.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160);
            const cardTxt = (card ? card.innerText : title).trim().replace(/\s+/g, ' ').slice(0, 240);
            if (title.length < 5 && cardTxt.length < 15) continue;
            if (!/engineer|developer|entwickler|stack|frontend|front-end|backend|back-end|typescript|javascript|react|vue|node|next|ai|llm|3d|webgl|software|web|cloud|it-/i.test(title + ' ' + cardTxt + ' ' + href)) continue;
            out.push({
              href,
              title: title || cardTxt.slice(0, 120),
              text: cardTxt || title,
            });
          }
          return out;
        }, linkRe);

        for (const it of items) {
          if (!byHref.has(it.href) || (!byHref.get(it.href).company && it.company)) {
            byHref.set(it.href, it);
          }
        }
      } catch (e) {}
    }
    results[portal] = [...byHref.values()];
    summary[portal] = results[portal].length;
  }

  await L.closeTab('harvester_bg');
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
  return { summary };
};
