const fs = require('fs');
const L = require('./lib.js');

const FORBIDDEN_EMAIL_RE = /\b(tailored|tailor|customi[sz]ed|bespoke|ats|keyword|delve|testament|underscore|seamlessly|aligns directly|standout match|pleased to apply|thrilled|excited|passionate|kindly|please forward|writing to express|leverage|leveraging|synergy|moreover|furthermore|spearheaded)\b|—/i;

/**
 * Builds a short, natural, human email body matching the EMAIL-APPLICATION STYLE rule:
 * - max ~120 words, 3 short paragraphs + signature, NO bullets, NO bold, <=3-4 techs, plain contractions ("I'm", "I'd").
 * - Reads candidate details dynamically from `candidate_profile.json`.
 */
function buildHumanEmailBody({ isGermanAd = true, roleTitle, refNo = '', productTieSentence, salaryLine = '' }) {
  const prof = L.loadCandidateProfile();
  const cand = prof.candidate || {};
  const edu = cand.education || {};
  const avail = cand.availability || {};
  const links = cand.links || {};

  const fullName = cand.full_name || 'Alex Morgan';
  const phone = cand.phone || '+49 170 0000000';
  const linkedin = links.linkedin_display || 'linkedin.com/in/alex-morgan-example';
  const degree = edu.current_degree || 'M.Sc. in Computer Science';
  const uni = edu.current_university || 'Technical University of Berlin';
  const grad = edu.graduation_month_year || 'November 2026';
  const startProse = avail.earliest_start_prose || '1 December 2026';

  const greeting = isGermanAd ? 'Guten Tag,' : 'Hello,';
  const refPart = refNo ? ` (${refNo})` : '';
  const p1 = `${greeting}\n\nI'm applying for the ${roleTitle} position${refPart}.`;
  const p2 = productTieSentence.trim();
  const sal = salaryLine ? ` ${salaryLine.trim()}` : '';
  const p3 = `I'm finishing my ${degree} at ${uni} in ${grad} and can start full-time on ${startProse}, with a valid work permit and happy to relocate.${sal} CV and cover letter are attached. I'd be glad to talk.`;
  const sig = [fullName, phone, linkedin].join('\n');

  const body = [p1, p2, p3, sig].join('\n\n');
  const subjectPrefix = isGermanAd ? 'Bewerbung' : 'Application';
  const subject = `${subjectPrefix}: ${roleTitle} - ${fullName}`;
  validateHumanEmail(subject, body);
  return { subject, body };
}

function validateHumanEmail(subject, body) {
  const mBody = body.match(FORBIDDEN_EMAIL_RE);
  if (mBody) {
    throw new Error(`BLOCKED EMAIL: forbidden AI/meta phrase "${mBody[0]}" detected in body.`);
  }
  const mSub = subject.replace(/–/g, '-').match(FORBIDDEN_EMAIL_RE);
  if (mSub) {
    throw new Error(`BLOCKED EMAIL: forbidden AI/meta phrase "${mSub[0]}" detected in subject.`);
  }
  if (/^\s*[-•*]\s+/m.test(body) || /\*\*/.test(body)) {
    throw new Error('BLOCKED EMAIL: bullet lists and bold formatting are forbidden in email body.');
  }
  const words = body.trim().split(/\s+/).length;
  if (words > 140) {
    throw new Error(`BLOCKED EMAIL: too long (${words} words > 140 max; target <=120 words).`);
  }
}

async function sendCleanApplicationEmail(browser, context, { to, cc = '', subject, body, files, confirmationShotPath }) {
  validateHumanEmail(subject, body);
  const prof = L.loadCandidateProfile();
  const filesCfg = (prof.candidate && prof.candidate.files) || {};
  const resName = filesCfg.resume_pdf_name || 'Alex_Morgan_Resume.pdf';
  const clName = filesCfg.cover_letter_pdf_name || 'Alex_Morgan_Cover_Letter.pdf';

  await L.closeTab('gmail_bg');
  const params = new URLSearchParams({ view: 'cm', fs: '1', to, su: subject });
  if (cc) params.set('cc', cc);

  const page = await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/?' + params.toString());
  await page.setViewportSize({ width: 1280, height: 900 }).catch(() => {});
  await page.waitForSelector('div[aria-label="Message Body"][contenteditable="true"], div[g_editable="true"], [contenteditable="true"][role="textbox"]', { timeout: 30000 });
  await page.waitForTimeout(800);

  await page.evaluate((text) => {
    const el = document.querySelector('div[aria-label="Message Body"][contenteditable="true"], div[g_editable="true"], [contenteditable="true"][role="textbox"]');
    if (!el) throw new Error('Gmail Message Body not found');
    el.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);
  }, body);
  await page.waitForTimeout(600);

  const fileInp = page.locator('input[name="Filedata"]').first();
  await fileInp.setInputFiles(files);

  let uploadedOk = false;
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(1000);
    const st = await page.evaluate(({ rName, cName }) => {
      const txt = document.body.innerText;
      const hasRes = txt.toLowerCase().includes(rName.toLowerCase());
      const hasCl = txt.toLowerCase().includes(cName.toLowerCase());
      const bars = [...document.querySelectorAll('[role="progressbar"]')].filter(b => b.offsetParent !== null).length;
      return { hasRes, hasCl, bars };
    }, { rName: resName, cName: clName });
    if (st.hasRes && st.hasCl && st.bars === 0) {
      uploadedOk = true;
      break;
    }
  }
  if (!uploadedOk) {
    await L.closeTab('gmail_bg');
    throw new Error('Attachment upload did not complete cleanly in Gmail');
  }

  const sendBtn = page.locator('div[role="button"][aria-label^="Send"]:not([aria-label*="options"])').last();
  await sendBtn.click({ timeout: 5000 }).catch(async () => {
    await page.evaluate(() => {
      const btns = [...document.querySelectorAll('div[role="button"][aria-label^="Send"]:not([aria-label*="options"])')];
      const b = btns[btns.length - 1];
      if (!b) throw new Error('Gmail Send button not found');
      b.click();
    });
  });
  await page.waitForTimeout(6000);

  await L.closeTab('gmail_bg');
  const gmSent = await L.getTab(browser, context, 'gmail_bg', 'https://mail.google.com/mail/u/0/#sent');
  await gmSent.waitForTimeout(4500);

  const sentRows = await gmSent.evaluate(() =>
    [...document.querySelectorAll('tr.zA')].filter(r => r.offsetParent !== null).slice(0, 3).map(tr => tr.innerText.replace(/\s+/g, ' ').trim())
  );

  if (confirmationShotPath) {
    try {
      const cdp = await context.newCDPSession(gmSent);
      const shot = await Promise.race([
        cdp.send('Page.captureScreenshot', { format: 'png' }),
        new Promise((_, rej) => setTimeout(() => rej(new Error('screenshot_timeout')), 4000))
      ]);
      fs.writeFileSync(confirmationShotPath, Buffer.from(shot.data, 'base64'));
    } catch (e) {}
  }

  await L.closeTab('gmail_bg');
  return { ok: true, sentTop: sentRows };
}

module.exports = { buildHumanEmailBody, validateHumanEmail, sendCleanApplicationEmail };
