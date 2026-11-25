const { closeTab } = require('./lib');
module.exports = async () => {
  const closed = [];
  for (const k of Object.keys(global.__tabs || {})) {
    try { await closeTab(k); closed.push(k); } catch (e) {}
  }
  return { closed };
};
