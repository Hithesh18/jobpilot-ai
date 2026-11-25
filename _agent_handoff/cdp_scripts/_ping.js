module.exports = async (browser, context) => ({ connected: browser.isConnected(), contexts: browser.contexts().length });
