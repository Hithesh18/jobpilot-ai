const L = require('./lib.js');

module.exports = async (browser, context) => {
  const gm = await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/#sent');
  await gm.waitForTimeout(3500);
  const sentRows = await gm.evaluate(() => {
    return [...document.querySelectorAll('tr.zA')].slice(0, 8).map(tr => tr.innerText.replace(/\s+/g, ' ').trim());
  });

  await gm.goto('https://mail.google.com/mail/u/0/#drafts', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await gm.waitForTimeout(3500);
  const draftRows = await gm.evaluate(() => {
    return [...document.querySelectorAll('tr.zA')].map((tr, i) => ({
      idx: i,
      text: tr.innerText.replace(/\s+/g, ' ').trim()
    }));
  });

  await L.closeTab('gmail_bg');
  return { sentRows, draftRows };
};
