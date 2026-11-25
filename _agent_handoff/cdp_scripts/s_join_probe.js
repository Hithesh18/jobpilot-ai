const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];

module.exports = async (browser, context) => {
  const p = await L.getTab(browser, context, 'sweep', 'https://join.com/jobs?countries=DE&q=Full%20Stack%20Developer');
  await p.waitForTimeout(4500);
  const joinProbe = await p.evaluate(() => {
    const links = [...document.querySelectorAll('a[href*="/companies/"]')].map(a => ({
      txt: a.innerText.replace(/\s+/g, ' ').trim().slice(0, 140),
      href: a.href
    }));
    const inputs = [...document.querySelectorAll('input, button, a')]
      .filter(e => /search|location|country|germany|filter|date|sort/i.test((e.placeholder || '') + ' ' + (e.innerText || '') + ' ' + (e.href || '')))
      .slice(0, 15)
      .map(e => ({
        tag: e.tagName,
        placeholder: e.placeholder || '',
        txt: (e.innerText || '').trim().slice(0, 60),
        href: e.href || ''
      }));
    return {
      url: location.href,
      title: document.title,
      count: links.length,
      sample: links.slice(0, 15),
      inputs,
      snippet: document.body.innerText.slice(0, 1200)
    };
  });

  await L.closeTab('sweep');
  return { join_probe: joinProbe };
};
