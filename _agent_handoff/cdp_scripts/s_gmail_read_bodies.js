const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const gm = await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/#inbox');
  await gm.waitForTimeout(4000);

  const targets = (process.env.GMAIL_ROW_INDICES || '0,1,2').split(',').map(x => parseInt(x.trim(), 10)).filter(n => !isNaN(n));
  const results = [];
  for (const idx of targets) {
    await gm.goto('https://mail.google.com/mail/u/0/#inbox', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await gm.waitForTimeout(2200);
    const clicked = await gm.evaluate((i) => {
      const tr = document.querySelectorAll('tr.zA')[i];
      if (!tr) return null;
      const subj = (tr.querySelector('.bog') || {}).innerText || '';
      tr.click();
      return subj;
    }, idx);
    await gm.waitForTimeout(2200);
    const body = await gm.evaluate(() => {
      const msgs = [...document.querySelectorAll('.a3s')];
      return msgs.map(m => (m.innerText || '').trim()).join('\n---\n').slice(0, 2000);
    });
    results.push({ idx, clicked, body });
  }

  await L.closeTab('gmail_bg');
  return results;
};
