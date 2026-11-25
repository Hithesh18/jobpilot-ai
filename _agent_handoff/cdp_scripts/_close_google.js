const L = require('./lib.js');
module.exports = async () => { await L.closeTab('google'); return { closed: true }; };
