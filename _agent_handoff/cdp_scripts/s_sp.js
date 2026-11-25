const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

const ATS_HOST = /(ashbyhq\.com|greenhouse\.io|lever\.co|personio\.(de|com)|workable\.com|recruitee\.com|smartrecruiters\.com|teamtailor\.com|join\.com)$/i;
const BAD_HOST = /(startpage\.com|ixquick\.com|yahoo\.com|brave\.com|google\.|bing\.com|duckduckgo\.com|msn\.com)$/i;

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_sp_cfg.json'), 'utf8').replace(/^\uFEFF/, ''));
  const p = await L.getTab(browser, context, 'sp');
  const byUrl = new Map();
  const log = [];
  const spDate = cfg.date || 'd';
  const yhDate = spDate === 'd' ? 'd' : (spDate === 'w' ? 'w' : 'm');

  const extractLinks = async () => {
    return await p.evaluate(({ atsSrc, badSrc }) => {
      const atsRe = new RegExp(atsSrc, 'i');
      const badRe = new RegExp(badSrc, 'i');
      const map = {};
      for (const a of document.querySelectorAll('a[href]')) {
        let href = a.href || '';
        const ru = href.match(/\/RU=([^/]+)\//);
        if (ru) {
          try { href = decodeURIComponent(ru[1]); } catch (e) {}
        }
        let uObj;
        try { uObj = new URL(href); } catch (e) { continue; }
        if (!/^https?:$/i.test(uObj.protocol)) continue;
        if (badRe.test(uObj.hostname)) continue;
        if (!atsRe.test(uObj.hostname)) continue;
        if (uObj.hostname.endsWith('join.com') && !uObj.pathname.startsWith('/companies/')) continue;

        const clean = (uObj.origin + uObj.pathname).replace(/\/+$/, '');
        const txt = (a.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160);
        const box = a.closest('.result, .w-gl__result, .algo, .dd, article, li, div[class*=result]') || a.parentElement;
        const snip = (box ? box.innerText : '').replace(/\s+/g, ' ').trim().slice(0, 360);
        if (!map[clean] || (!map[clean].t && txt)) {
          map[clean] = { u: clean, t: txt || (map[clean] ? map[clean].t : ''), s: snip || (map[clean] ? map[clean].s : '') };
        }
      }
      return Object.values(map);
    }, { atsSrc: ATS_HOST.source, badSrc: BAD_HOST.source });
  };

  let spBlocked = false;
  for (const q of cfg.queries) {
    if (!spBlocked) {
      for (const page of (cfg.pages || [1])) {
        const u = 'https://www.startpage.com/do/search?q=' + encodeURIComponent(q) + '&with_date=' + spDate + '&page=' + page;
        try {
          await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 35000 });
          await p.waitForTimeout(2200 + Math.random() * 1200);
          const bodyHead = await p.evaluate(() => (document.body ? document.body.innerText.slice(0, 600) : ''));
          if (/captcha/i.test(p.url()) || /captcha|unusual traffic|verify you are human/i.test(bodyHead)) {
            log.push(['sp', q.slice(0, 55), page, 'CAPTCHA_SWITCH_YAHOO']);
            spBlocked = true;
            break;
          }
          const r = await extractLinks();
          r.forEach(x => {
            if (!byUrl.has(x.u) || (!byUrl.get(x.u).t && x.t)) byUrl.set(x.u, { q, engine: 'startpage', ...x });
          });
          log.push(['sp', q.slice(0, 55), page, r.length]);
          if (r.length < 6) break;
        } catch (e) {
          log.push(['sp', q.slice(0, 55), page, 'ERR ' + e.message.slice(0, 60)]);
          break;
        }
      }
    }

    if (spBlocked || cfg.includeYahoo !== false) {
      for (const page of (cfg.pages || [1])) {
        const b = (page - 1) * 10 + 1;
        const u = 'https://de.search.yahoo.com/search?p=' + encodeURIComponent(q) + '&btf=' + yhDate + '&b=' + b;
        try {
          await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 35000 });
          await p.waitForTimeout(1800 + Math.random() * 1000);
          const clickedConsent = await p.evaluate(() => {
            const btn = [...document.querySelectorAll('button')].find(b => /alle akzeptieren|accept all|agree/i.test(b.innerText || ''));
            if (btn) { btn.click(); return true; }
            return false;
          });
          if (clickedConsent) await p.waitForTimeout(2000);
          const r = await extractLinks();
          r.forEach(x => {
            if (!byUrl.has(x.u) || (!byUrl.get(x.u).t && x.t)) byUrl.set(x.u, { q, engine: 'yahoo', ...x });
          });
          log.push(['yh', q.slice(0, 55), page, r.length]);
          if (r.length < 5) break;
        } catch (e) {
          log.push(['yh', q.slice(0, 55), page, 'ERR ' + e.message.slice(0, 60)]);
          break;
        }
      }
    }
  }

  const out = [...byUrl.values()];
  fs.writeFileSync(path.join(L.HANDOFF_DIR, '_sp_out.json'), JSON.stringify(out, null, 1));
  return { log, n: out.length, spBlocked };
};
