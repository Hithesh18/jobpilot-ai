const fs = require('fs');
const os = require('os');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright');

function findDevToolsPortFile() {
  if (process.env.CHROME_DEVTOOLS_PORT_FILE) return process.env.CHROME_DEVTOOLS_PORT_FILE;
  if (process.platform === 'win32' && process.env.LOCALAPPDATA) {
    return path.join(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort');
  }
  if (process.platform === 'darwin') {
    return path.join(os.homedir(), 'Library', 'Application Support', 'Google', 'Chrome', 'DevToolsActivePort');
  }
  return path.join(os.homedir(), '.config', 'google-chrome', 'DevToolsActivePort');
}

async function resolveEndpoint() {
  if (process.env.CDP_URL) return process.env.CDP_URL;
  const port9222Ok = await new Promise(resolve => {
    const req = http.get('http://127.0.0.1:9222/json/version', { timeout: 1500 }, res => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
  if (port9222Ok) return 'http://127.0.0.1:9222';
  const portFile = findDevToolsPortFile();
  const lines = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  return `ws://127.0.0.1:${lines[0]}${lines[1]}`;
}

(async () => {
  const scriptPath = process.argv[2];
  const outPath = process.argv[3];
  const endpoint = await resolveEndpoint();
  const browser = await chromium.connectOverCDP(endpoint, { timeout: 60000 });
  const context = browser.contexts()[0];
  const fn = require(path.resolve(scriptPath));
  const result = await fn(browser, context);
  fs.writeFileSync(outPath, JSON.stringify({ ok: true, result }, null, 2), 'utf8');
  process.exit(0);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
