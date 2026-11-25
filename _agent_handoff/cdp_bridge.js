/**
 * Persistent Silent Chrome CDP Bridge (`_agent_handoff/cdp_bridge.js`)
 * Listens on http://127.0.0.1:9333 and executes background tab step scripts (`cdp_scripts/*.js`)
 * inside the user's running Chrome session (`Target.createTarget({ background: true })` +
 * `Emulation.setFocusEmulationEnabled({ enabled: true })`) with ZERO popups or focus stealing.
 *
 * Connection order:
 *   1. `CDP_URL` env var (e.g. `http://127.0.0.1:9222` when Chrome is started with `--remote-debugging-port=9222`)
 *   2. `http://127.0.0.1:9222` (if reachable)
 *   3. Chrome's `DevToolsActivePort` file (`chrome://inspect/#remote-debugging` enabled) across Windows, macOS, and Linux.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright');

let browser = null;
let context = null;

function findDevToolsPortFile() {
  const candidates = [];
  if (process.env.CHROME_DEVTOOLS_PORT_FILE) {
    candidates.push(process.env.CHROME_DEVTOOLS_PORT_FILE);
  }
  if (process.platform === 'win32' && process.env.LOCALAPPDATA) {
    candidates.push(path.join(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'User Data', 'DevToolsActivePort'));
  } else if (process.platform === 'darwin') {
    candidates.push(path.join(os.homedir(), 'Library', 'Application Support', 'Google', 'Chrome', 'DevToolsActivePort'));
  } else {
    candidates.push(path.join(os.homedir(), '.config', 'google-chrome', 'DevToolsActivePort'));
    candidates.push(path.join(os.homedir(), '.config', 'chromium', 'DevToolsActivePort'));
  }
  return candidates.find(p => fs.existsSync(p)) || null;
}

async function resolveCdpEndpoint() {
  if (process.env.CDP_URL) return process.env.CDP_URL;

  // Check standard --remote-debugging-port=9222 first
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
  if (!portFile) {
    throw new Error(
      'Could not find Chrome remote debugging endpoint. Start Chrome with `--remote-debugging-port=9222` ' +
      'or enable remote debugging in `chrome://inspect/#remote-debugging`.'
    );
  }
  const lines = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/);
  return `ws://127.0.0.1:${lines[0]}${lines[1]}`;
}

async function ensureConnected() {
  if (browser && browser.isConnected() && context && browser.contexts().length > 0) {
    return { browser, context };
  }
  const endpoint = await resolveCdpEndpoint();
  console.log('Connecting persistent bridge to:', endpoint);
  browser = await chromium.connectOverCDP(endpoint, { timeout: 0 });
  context = browser.contexts()[0];
  global.__tabs = {};
  console.log('BRIDGE_CONNECTED_OK! Open pages:', context.pages().length);
  return { browser, context };
}

(async () => {
  await ensureConnected();

  const server = http.createServer(async (req, res) => {
    if (req.method !== 'POST') {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      return res.end('OK');
    }
    let body = '';
    req.on('data', chunk => (body += chunk));
    req.on('end', async () => {
      try {
        const conn = await ensureConnected();
        const { scriptPath } = JSON.parse(body);
        delete require.cache[require.resolve(scriptPath)];
        const fn = require(scriptPath);
        const result = await fn(conn.browser, conn.context);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message, stack: err.stack }));
      }
    });
  });

  server.listen(9333, '127.0.0.1', () => {
    console.log('BRIDGE_LISTENING_ON_127.0.0.1:9333');
  });
})().catch(err => {
  console.error('Bridge fatal error:', err);
  process.exit(1);
});
