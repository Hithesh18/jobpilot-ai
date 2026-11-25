const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const gm = await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/#inbox');
  await gm.waitForTimeout(4500);

  const rows = await gm.evaluate(() => {
    const trs = [...document.querySelectorAll('tr.zA')].slice(0, 50);
    return trs.map((tr, idx) => {
      const senderEl = tr.querySelector('.yW span[email], .yW span');
      const senderName = senderEl ? (senderEl.innerText || senderEl.getAttribute('name') || '').trim() : '';
      const senderEmail = senderEl ? (senderEl.getAttribute('email') || '').trim() : '';
      const subjEl = tr.querySelector('.bog');
      const subject = subjEl ? (subjEl.innerText || '').trim() : '';
      const snipEl = tr.querySelector('.y2');
      const snippet = snipEl ? (snipEl.innerText || '').replace(/^\s*-\s*/, '').trim() : '';
      const timeEl = tr.querySelector('td.xW span');
      const time = timeEl ? (timeEl.getAttribute('title') || timeEl.innerText || '').trim() : '';
      const unread = tr.classList.contains('zE');
      return { idx, unread, time, senderName, senderEmail, subject, snippet };
    });
  });

  const appRe = /\b(application|bewerbung|vacancy|position|role|stelle|feedback|update|candidate|interview)\b/i;
  const ignoreRe = /\b(linkedin job alerts|xing jobs|talent\.com|stepstone daily|jobleads|hokify|mailsuite|quora)\b/i;
  const obviousRe = /\b(unfortunately|not to move forward|not be moving forward|other candidates|isn't an ideal fit|don't see an ideal fit|regret to inform|closing this position|automatic reply)\b/i;

  for (const r of rows.slice(0, 25)) {
    const comb = `${r.senderName} ${r.subject} ${r.snippet}`;
    if (appRe.test(comb) && !ignoreRe.test(r.senderName) && !obviousRe.test(r.snippet)) {
      try {
        await gm.goto('https://mail.google.com/mail/u/0/#inbox', { waitUntil: 'domcontentloaded', timeout: 45000 });
        await gm.waitForTimeout(2200);
        await gm.evaluate((i) => {
          const tr = document.querySelectorAll('tr.zA')[i];
          if (tr) tr.click();
        }, r.idx);
        await gm.waitForTimeout(2200);
        const fullBody = await gm.evaluate(() => {
          const msgs = [...document.querySelectorAll('.a3s')];
          return msgs.map(m => (m.innerText || '').replace(/\s+/g, ' ').trim()).join(' | ').slice(0, 1200);
        });
        if (fullBody) {
          r.snippet = `${r.snippet} || FULL_BODY: ${fullBody}`;
        }
      } catch (e) {}
    }
  }

  await L.closeTab('gmail_bg');
  return { count: rows.length, rows };
};
