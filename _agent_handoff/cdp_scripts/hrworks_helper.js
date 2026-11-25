// Reusable HRworks (/en/apply or /de/apply) helper that fills ALL fields from `candidate_profile.json`
// including Earliest possible join date & Birthday and asserts non-empty readback before clicking Submit -> Yes.
const fs = require('fs');
const L = require('./lib.js');

async function fillAndSubmitHRworks(browser, context, {
  tabName = 'hrworks_bg',
  url,
  salary,
  remark = '',
  files = [],
  confirmationShotPath = ''
}) {
  const prof = L.loadCandidateProfile();
  const cand = prof.candidate || {};
  const addr = cand.address || {};
  const avail = cand.availability || {};
  const compCfg = cand.compensation || {};

  const firstName = cand.first_name || 'Alex';
  const lastName = cand.last_name || 'Morgan';
  const email = cand.email || 'alex.morgan.dev@example.com';
  const phone = cand.phone || '+49 170 0000000';
  const salVal = salary || compCfg.default_number || '65000';

  await L.closeTab(tabName);
  const page = await L.getTab(browser, context, tabName, url);
  await page.setViewportSize({ width: 1280, height: 1100 }).catch(() => {});
  await page.waitForTimeout(3000);

  await page.evaluate(() => {
    for (const f of document.querySelectorAll('.page-footer')) f.style.pointerEvents = 'none';
  });

  const isGermanForm = await page.evaluate(() => /\/de\//i.test(location.pathname) || /Vorname\s*:/i.test(document.body.innerText));
  const joinDateVal = isGermanForm ? (avail.earliest_start_de || '01.12.2026') : (avail.earliest_start_us || '12/01/2026');
  const birthDateVal = isGermanForm ? (cand.date_of_birth_de || '15.06.2000') : (cand.date_of_birth_us || '06/15/2000');

  const ids = await page.evaluate(() => {
    const out = {};
    const els = [...document.querySelectorAll('input:not([type="hidden"]), select, textarea')];
    for (const el of els) {
      const row = el.closest('tr, .form-group, .row, div[class*="field"], div[class*="row"]') || el.parentElement.parentElement;
      const ctx = (row ? row.innerText : el.parentElement.innerText || '').replace(/\s+/g, ' ').trim();
      const idSel = '[id="' + el.id + '"]';
      if (/^(Salutation|Anrede)\s*:/i.test(ctx) && el.tagName === 'SELECT') out.salutation = idSel;
      else if (/^(First name|Vorname)\s*:/i.test(ctx)) out.firstName = idSel;
      else if (/^(Last name|Nachname)\s*:/i.test(ctx)) out.lastName = idSel;
      else if (/^(Email|E-Mail)\s*:/i.test(ctx)) out.email = idSel;
      else if (/^(Phone|Telephone|Mobile|Telefon|Handy)\s*:/i.test(ctx)) out.phone = idSel;
      else if (/^(Street|Straße)\s*:/i.test(ctx)) out.street = idSel;
      else if (/^(Street number|Hausnummer)\s*:/i.test(ctx)) out.streetNo = idSel;
      else if (/^(Additional|Adresszusatz)\s*:/i.test(ctx)) out.additional = idSel;
      else if (/^(Country|Land)\s*:/i.test(ctx) && el.tagName === 'SELECT') out.country = idSel;
      else if (/^(ZIP Code|PLZ|Postleitzahl)\s*:/i.test(ctx)) out.zip = idSel;
      else if (/^(Location|Ort|Stadt)\s*:/i.test(ctx)) out.city = idSel;
      else if (/^(Birthday|Geburtsdatum)\s*:/i.test(ctx)) out.birthday = idSel;
      else if (/^(Desired annual salary|Gehaltswunsch|Gehaltsvorstellung)/i.test(ctx)) out.salary = idSel;
      else if (/^(Earliest possible join date|Frühestmöglicher Eintrittstermin|Possible start date)/i.test(ctx)) out.joinDate = idSel;
      else if (/^(Notice period|Kündigungsfrist)\s*:/i.test(ctx) && el.tagName === 'INPUT' && el.type === 'text') out.noticeNum = idSel;
      else if (/Days.*Weeks.*Months|Tage.*Wochen.*Monate/i.test(ctx) && el.tagName === 'SELECT') out.noticeUnit = idSel;
      else if (/^(How did you hear|Wie sind Sie auf uns)/i.test(ctx) && el.tagName === 'SELECT') out.source = idSel;
      else if (/^(Remark|Bemerkung|Nachricht)\s*:/i.test(ctx) && el.tagName === 'TEXTAREA') out.remark = idSel;
    }
    const sub = [...document.querySelectorAll('a, button')].find(e => /^(Submit application|Bewerbung absenden)$/i.test((e.innerText || '').trim()));
    if (sub) out.submitId = '[id="' + sub.id + '"]';
    return out;
  });

  const fillWicket = async (sel, val) => {
    if (!sel || !val) return;
    const loc = page.locator(sel);
    await loc.click({ force: true });
    await loc.fill(val);
    await page.keyboard.press('Escape').catch(() => {});
    await page.keyboard.press('Tab');
    await page.waitForTimeout(250);
  };

  if (ids.salutation) {
    const salLabel = isGermanForm ? (cand.salutation_de || 'Herr') : (cand.salutation_en || 'Mr.');
    await page.locator(ids.salutation).selectOption({ label: salLabel }).catch(() => {});
    await page.waitForTimeout(350);
  }
  await fillWicket(ids.firstName, firstName);
  await fillWicket(ids.lastName, lastName);
  await fillWicket(ids.email, email);
  await fillWicket(ids.phone, phone);
  await fillWicket(ids.street, addr.street || 'Torstrasse');
  await fillWicket(ids.streetNo, addr.street_number || '120');
  await fillWicket(ids.additional, addr.additional || '');
  if (ids.country) {
    const cLabel = isGermanForm ? (addr.country_de || 'Deutschland') : (addr.country || 'Germany');
    await page.locator(ids.country).selectOption({ label: cLabel }).catch(() => {});
    await page.waitForTimeout(450);
  }
  await fillWicket(ids.zip, addr.postal_code || '10119');
  await fillWicket(ids.city, addr.city || 'Berlin');
  await fillWicket(ids.birthday, birthDateVal);
  await fillWicket(ids.salary, salVal);
  await fillWicket(ids.joinDate, joinDateVal);
  await fillWicket(ids.noticeNum, avail.notice_period_number || '2');
  if (ids.noticeUnit) {
    const uLabel = isGermanForm ? (avail.notice_period_unit_de || 'Wochen') : (avail.notice_period_unit_en || 'Weeks');
    await page.locator(ids.noticeUnit).selectOption({ label: uLabel }).catch(() => {});
    await page.waitForTimeout(300);
  }
  if (ids.source) {
    await page.locator(ids.source).evaluate((s) => {
      const opt = [...s.options].find(o => /federal employment|arbeitsagentur|company website|other|sonstige/i.test(o.text));
      if (opt) {
        s.value = opt.value;
        s.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await page.waitForTimeout(350);
  }
  if (remark) await fillWicket(ids.remark, remark);

  const readback = await page.evaluate((idsObj) => {
    const valOf = (sel) => {
      if (!sel) return null;
      const el = document.querySelector(sel);
      return el ? el.value : null;
    };
    return {
      firstName: valOf(idsObj.firstName),
      lastName: valOf(idsObj.lastName),
      joinDate: valOf(idsObj.joinDate),
      birthday: valOf(idsObj.birthday),
      salary: valOf(idsObj.salary)
    };
  }, ids);

  if (readback.firstName !== firstName || readback.lastName !== lastName) {
    await L.closeTab(tabName);
    throw new Error(`HRworks Name Readback Failed: ${JSON.stringify(readback)}`);
  }
  if (ids.joinDate && (!readback.joinDate || !readback.joinDate.trim())) {
    await L.closeTab(tabName);
    throw new Error(`HRworks Join Date Readback Empty! Refusing to submit without start date: ${JSON.stringify(readback)}`);
  }

  await page.evaluate(() => {
    for (const cb of document.querySelectorAll('input[type="checkbox"]')) {
      const row = cb.parentElement ? cb.parentElement.parentElement : null;
      const txt = (row ? row.innerText : '').toLowerCase();
      if ((txt.includes('talent pool') || txt.includes('corporate group') || txt.includes('privacy') || txt.includes('datenschutz')) && !cb.checked) {
        cb.click();
      }
    }
  });
  await page.waitForTimeout(400);

  for (const f of files) {
    await page.locator('input[type="file"]').first().setInputFiles(f.path);
    for (let i = 0; i < 25; i++) {
      await page.waitForTimeout(900);
      const ok = await page.evaluate((p) => new RegExp(p, 'i').test(document.body.innerText), f.pat);
      if (ok) break;
    }
  }
  await page.waitForTimeout(800);

  await page.locator(ids.submitId || 'a:has-text("Submit application"), a:has-text("Bewerbung absenden")').first().click({ force: true });
  await page.waitForTimeout(2500);

  const clickedYes = await page.evaluate(() => {
    const yesEl = [...document.querySelectorAll('a, button')].find(e => /^(Yes|Ja)$/i.test((e.innerText || '').trim()) && e.offsetParent !== null);
    if (yesEl) {
      yesEl.click();
      return { ok: true, id: yesEl.id };
    }
    return { ok: false };
  });
  if (clickedYes.ok && clickedYes.id) {
    await page.waitForTimeout(600);
    await page.locator('[id="' + clickedYes.id + '"]').click({ force: true }).catch(() => {});
  }

  await page.waitForTimeout(8000);
  const after = await page.evaluate(() => {
    const txt = ((document.body && document.body.innerText) || '').replace(/\s+/g, ' ').trim();
    return {
      url: location.href,
      submitted: /thank you|successfully|received your application|vielen dank|eingegangen|erhalten/i.test(txt),
      snippet: txt.slice(0, 1000)
    };
  });

  if (confirmationShotPath) {
    try {
      const cdp = await context.newCDPSession(page);
      const shot = await Promise.race([
        cdp.send('Page.captureScreenshot', { format: 'png' }),
        new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 3500))
      ]);
      fs.writeFileSync(confirmationShotPath, Buffer.from(shot.data, 'base64'));
    } catch (e) {}
  }

  await L.closeTab(tabName);
  return { readback, after };
}

module.exports = { fillAndSubmitHRworks };
