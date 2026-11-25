const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const gm = global.__tabs['gmail_bg'] || await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/#inbox');
  await gm.evaluate(() => {
    const c = [...document.querySelectorAll('[role="button"]')].find(b => /^compose$/i.test((b.innerText || '').trim()));
    if (c) c.click();
  });
  await gm.waitForTimeout(2500);
  return await gm.evaluate(() => {
    const dlg = document.querySelector('[role="dialog"]') || document.body;
    const els = [...dlg.querySelectorAll('input, textarea, [contenteditable="true"], [role="button"]')].map(e => ({
      tag: e.tagName,
      type: e.type || '',
      name: e.name || '',
      aria: e.getAttribute('aria-label') || '',
      txt: (e.innerText || '').trim().slice(0, 40)
    }));
    const fileInps = [...document.querySelectorAll('input[type="file"]')].map(f => ({ name: f.name, accept: f.accept, multiple: f.multiple }));
    return { hasDialog: !!document.querySelector('[role="dialog"]'), els: els.slice(0, 35), fileInps };
  });
};
