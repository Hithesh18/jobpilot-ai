const L = require('./lib.js');
delete require.cache[require.resolve('./lib.js')];
module.exports = async () => {
  const closed = [];
  for (const n of ['bing', 'sp', 'alt', 'dex', 'google']) {
    if (global.__tabs[n]) {
      await L.closeTab(n);
      closed.push(n);
    }
  }
  return closed;
};
