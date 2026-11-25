const fs = require('fs');
const path = require('path');
const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '_links_cfg.json'), 'utf8').replace(/^\uFEFF/, ''));
  const p = await L.getTab(browser, context, 'links');
  const out = {};
  const log = [];
  for (const u of cfg.urls) {
    try {
      await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(1800);
      const r = await p.evaluate(() => [...document.querySelectorAll('div.js-job')].map(c => {
        const a = c.querySelector('a.js-joblink');
        const li = [...c.querySelectorAll('li')].map(x => x.innerText.trim());
        return {
          id: c.id,
          title: (c.querySelector('h3') || {}).innerText,
          company: li[0] || '',
          loc: li[1] || '',
          age: li.slice(2).join(' / '),
          src: a ? a.getAttribute('source') : '',
          url: a ? a.href : ''
        };
      }));
      r.forEach(x => { out[x.id] = x; });
      log.push([u.slice(-45), r.length]);
    } catch (e) {
      log.push([u.slice(-45), 'ERR ' + e.message.slice(0, 80)]);
    }
  }
  fs.writeFileSync(path.join(L.HANDOFF_DIR, '_ej_out.json'), JSON.stringify(out, null, 1));
  return { log: log.map(x => x.join(':')).join(' '), n: Object.keys(out).length };
};
