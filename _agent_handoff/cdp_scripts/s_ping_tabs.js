module.exports = async () => {
  const tabs = {};
  for (const [k, p] of Object.entries(global.__tabs || {})) {
    if (p && !p.isClosed()) {
      tabs[k] = {
        url: p.url(),
        text: await p.evaluate(() => (document.body ? document.body.innerText.slice(0, 1200) : '')).catch(() => '')
      };
    }
  }
  return tabs;
};
