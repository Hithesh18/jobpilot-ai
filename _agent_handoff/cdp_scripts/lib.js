// Shared helpers for CDP bridge background step scripts (Claude Code & Gemini Antigravity).
// Tabs open strictly in background with focus emulation so zero popups steal user focus.
const fs = require('fs');
const path = require('path');

const HANDOFF_DIR = path.resolve(__dirname, '..');
const WORKSPACE_ROOT = path.resolve(HANDOFF_DIR, '..');
const PROFILE_PATH = path.join(WORKSPACE_ROOT, 'candidate_profile.json');

global.__tabs = global.__tabs || {};

function loadCandidateProfile() {
  try {
    if (fs.existsSync(PROFILE_PATH)) {
      return JSON.parse(fs.readFileSync(PROFILE_PATH, 'utf8').replace(/^\uFEFF/, ''));
    }
  } catch (e) {}
  return {
    candidate: {
      first_name: 'Alex',
      last_name: 'Morgan',
      full_name: 'Alex Morgan',
      salutation_en: 'Mr.',
      salutation_de: 'Herr',
      email: 'alex.morgan.dev@example.com',
      phone: '+49 170 0000000',
      date_of_birth_de: '15.06.2000',
      date_of_birth_us: '06/15/2000',
      address: {
        street: 'Torstrasse',
        street_number: '120',
        additional: 'Apt 4B',
        postal_code: '10119',
        city: 'Berlin',
        country: 'Germany',
        country_de: 'Deutschland'
      },
      links: {
        linkedin_display: 'linkedin.com/in/alex-morgan-example'
      },
      education: {
        current_degree: 'M.Sc. in Computer Science',
        current_university: 'Technical University of Berlin',
        graduation_month_year: 'November 2026'
      },
      availability: {
        earliest_start_de: '01.12.2026',
        earliest_start_us: '12/01/2026',
        earliest_start_prose: '1 December 2026',
        notice_period_number: '2',
        notice_period_unit_en: 'Weeks',
        notice_period_unit_de: 'Wochen'
      },
      files: {
        resume_pdf_name: 'Alex_Morgan_Resume.pdf',
        cover_letter_pdf_name: 'Alex_Morgan_Cover_Letter.pdf'
      }
    }
  };
}

async function getTab(browser, context, name, url) {
  let p = global.__tabs[name];
  if (p && !p.isClosed()) {
    if (url) await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    return p;
  }
  const cdp = await browser.newBrowserCDPSession();
  const waitPage = context.waitForEvent('page', { timeout: 30000 });
  await cdp.send('Target.createTarget', { url: 'about:blank', background: true });
  p = await waitPage;
  try {
    const s = await context.newCDPSession(p);
    await s.send('Emulation.setFocusEmulationEnabled', { enabled: true });
  } catch (e) {}
  global.__tabs[name] = p;
  if (url) await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  return p;
}

async function closeTab(name) {
  const p = global.__tabs[name];
  if (p && !p.isClosed()) await p.close();
  delete global.__tabs[name];
}

// Compact snapshot of visible interactive elements + text across frames
async function snap(page, opts = {}) {
  const out = [];
  for (const f of page.frames()) {
    try {
      const r = await f.evaluate((maxText) => {
        const vis = e => {
          const s = getComputedStyle(e);
          const b = e.getBoundingClientRect();
          return s.display !== 'none' && s.visibility !== 'hidden' && (b.width > 0 || b.height > 0 || e.type === 'file' || e.type === 'checkbox' || e.type === 'radio');
        };
        const lab = e => {
          let t = '';
          if (e.id) {
            const l = document.querySelector(`label[for="${CSS.escape(e.id)}"]`);
            if (l) t = l.innerText;
          }
          if (!t && e.closest('label')) t = e.closest('label').innerText;
          return (t || e.getAttribute('aria-label') || e.placeholder || '').trim().slice(0, 120);
        };
        const items = [];
        document.querySelectorAll('input,select,textarea,button,a[role=button],[role=combobox],[role=checkbox],[role=radio]').forEach(e => {
          if (!vis(e) || e.type === 'hidden') return;
          let v = e.value;
          if (e.type === 'checkbox' || e.type === 'radio') v = e.checked;
          if (e.tagName === 'SELECT') v = e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : '';
          items.push(`${e.tagName.toLowerCase()}${e.type ? '[' + e.type + ']' : ''}#${e.id || ''} name=${e.name || ''} lab="${lab(e)}" txt="${(e.innerText || '').trim().slice(0, 60)}" val=${JSON.stringify(v === undefined ? '' : String(v).slice(0, 60))}${e.required ? ' REQ' : ''}${e.disabled ? ' DIS' : ''}`);
        });
        return {
          url: location.href,
          title: document.title,
          text: (document.body ? document.body.innerText : '').replace(/\n\s*\n+/g, '\n').slice(0, maxText),
          items
        };
      }, opts.maxText || 3000);
      if (r.items.length || f === page.mainFrame()) out.push(r);
    } catch (e) {}
  }
  return out;
}

module.exports = { getTab, closeTab, snap, loadCandidateProfile, HANDOFF_DIR, WORKSPACE_ROOT };
