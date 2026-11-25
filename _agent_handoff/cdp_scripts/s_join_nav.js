const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const p = await L.getTab(browser, context, 'sweep', 'https://join.com/talent/home');
  await p.waitForTimeout(2500);
  const nav = await p.evaluate(() => [...document.querySelectorAll('a[href], button')].map(e => ({
    tag: e.tagName,
    txt: (e.innerText || '').trim().slice(0, 80),
    href: e.href || ''
  })).slice(0, 40));

  await p.evaluate(() => {
    const m = [...document.querySelectorAll('button')].find(b => /menu/i.test(b.innerText));
    if (m) m.click();
  });
  await p.waitForTimeout(1000);
  const navAfterMenu = await p.evaluate(() => [...document.querySelectorAll('a[href]')].map(a => ({
    txt: (a.innerText || '').trim().slice(0, 80),
    href: a.href
  })).slice(0, 40));

  return { url: p.url(), nav, navAfterMenu };
};
