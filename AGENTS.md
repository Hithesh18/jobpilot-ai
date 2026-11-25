> **LANGUAGE REQUIREMENT RULE: A non-English JD is NOT an automatic skip.** Read the JD's actual spoken-language requirement: for candidates at `A2` German (default in `candidate_profile.json`), SKIP only if German is REQUIRED at `B1+` / `"gute / sehr gute / fließende Deutschkenntnisse"` / `"Deutsch in Wort und Schrift"` / `"good/fluent German"`. If German is `"von Vorteil / wünschenswert / a plus"` or not mentioned, a German-written JD is **GREEN** (apply with the English CV). German role titles (`Entwickler`, `:in`) are NOT auto-blocked. Enforced in `ats_poll.german_requirement()`, `auto_tailor.GERMAN_KO`, `li_sweep.py`, and `ba_sweep.py`.
> **ACCOUNT-SAFETY RULE: protect LinkedIn / StepStone / XING accounts.** (1) LinkedIn search + JD reading ONLY via the public guest API (`li_sweep.py`, `li_jd.py`) — never browse LinkedIn job pages mass-scraping in the logged-in Chrome (`s_fetch_jd.js` and `s_fetch.js` refuse `linkedin.com` URLs). (2) The logged-in-Chrome portal scrape (`harvest_all_portals.py` CDP part: StepStone/XING/Indeed/Jobvector/Glassdoor) runs at most every 30 min (`realtime_iter.sh` 25-min stamp) with 5–9 s random gaps; public HTML portals are swept WITHOUT login via `public_portals.py` (one parallel worker per portal). (3) `harvest_all_portals.py` skips LinkedIn unless `HARVEST_LI=1` is explicitly set. Logged-in sessions are reserved for **APPLYING**, not mass scraping.
> **EMAIL-APPLICATION STYLE ("looks human-written, never AI").** Every email application body must read like a person wrote it: max ~120 words, 3 short paragraphs + signature, NO bullet lists, NO bold, at most 3–4 technologies, ONE concrete link to the company's product, plain contractions (`"I'm"`, `"I'd"`). Banned phrases: `"kindly"`, `"please forward"`, `"excited/thrilled/passionate"`, `"I am writing to express"`, `"leverage"`, `"synergy"`, em-dashes (`—`), long tech lists. Structure: (1) `"Guten Tag,"` (German ad) or `"Hello,"` + one line naming the role (+ ref no.); (2) 2 sentences: what the candidate builds now (per `candidate_profile.json` & `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`) tied to the company's product; (3) degree/graduation & earliest start date, work authorization, relocation openness, salary ONLY if the ad asks, then `"CV and cover letter are attached. I'd be glad to talk."` Signature: full name, phone, LinkedIn from `candidate_profile.json`. Enforced by `_agent_handoff/cdp_scripts/gmail_helper.js`.
> **DAILY APPLIED JOBS SUMMARY FORMAT RULE:** Whenever the user asks for today's applied jobs, daily details, or an application summary, ALWAYS report the exact **total count applied today** at the top followed by a clean Markdown table with columns: **`#` | `App ID` | `Company` | `Role` | `Tech Stack` | `ATS Score` | `ATS / Portal`**.
> **COHERENT REAL-EXPERIENCE TAILORING RULE:** NEVER blindly paste or graft JD domain buzzwords, phrases, or unverified claims onto the candidate's Summary, Experience bullets, Thesis, Projects, or Cover Letter. Every sentence MUST make 100% logical and factual sense against `candidate_profile.json`, `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`, and `_agent_handoff/MASTER_RESUME_TEMPLATE.tex`. Never rename an employer's actual product domain (e.g., cloud SaaS metering, event ticketing, enterprise billing, 3D scene visualization, neighborhood portal) into unrelated JD domains, and never cross-contaminate tools across employers. Tailor by highlighting genuinely overlapping technologies and engineering problems actually solved.
> **100% HUMANIZED COVER LETTER RULE:** Every `<Candidate>_Cover_Letter.pdf` MUST read like a real engineer wrote it in plain, natural paragraphs: **ZERO dashes (`—`, `–`, `--`, `---`, or spaced ` - `)**, **ZERO bullet lists (`•` / `\begin{itemize}`)**, **ZERO bold subheadings inside paragraphs**, **ZERO semicolons**, and **ZERO AI clichés** (`"passionate"`, `"thrilled"`, `"excited"`, `"delighted"`, `"leverage"`, `"synergy"`, `"seamlessly"`, `"cutting-edge"`, `"at the intersection of"`, `"thrive in"`, `"aligns directly"`, `"uniquely positioned"`, `"I am writing to express"`, `"tailored"`, `"customized"`). Use natural contractions (`"I'm"`, `"I've"`, `"I'd"`), plain sentences, and concrete real work (`validate_resume_pdf.py` + `auto_tailor.py` enforce this automatically).

# JobPilot AI — Autonomous Job Discovery, Filtering, ATS Tailoring & Silent Background Application Engine
## Shared Single Brain for Claude Code (VS Code / CLI) & Gemini (Antigravity)

> **Multi-Agent Synchronization Contract:** You can alternate seamlessly between **Claude Code** and **Gemini (Antigravity)** on this exact repository whenever session tokens or quotas expire. Both agents stay 100% synchronized via `candidate_profile.json`, `Application_Tracker.xlsx`, `Manual_Apply_Queue.xlsx`, `_agent_handoff/sweep_state.json`, `_agent_handoff/sync_status.py`, and per-job `<Company>_<Role>/` folders.
> **SILENT BACKGROUND EXECUTION & ACCOUNT RULES:**
> 1. **Native Binaries Only:** Run native `python` (`sys.executable` or `PYTHON_EXE`), `tectonic` (`_agent_handoff/bin/tectonic[.exe]` auto-installed by `init_workspace.py`), and `node` (avoid heavy WSL wrappers on Windows).
> 2. **Silent Browser Execution (`cdp_bridge.js` on `http://127.0.0.1:9333` OR `headless_browser.py`):** Open tabs strictly in the background via `_agent_handoff/cdp_bridge.js` (`Target.createTarget` with `background: true` + `Emulation.setFocusEmulationEnabled` so zero popups or focus-stealing occur while the user works!). Prefer "Sign in with Google" when creating **NEW** portal accounts; otherwise generate a strong unique password and append immediately to `_private_account_logins.txt` (gitignored). Never reset passwords on pre-existing old accounts (route those to `Manual_Apply_Queue.xlsx`).

> **Universal Profession & Country Configurability:** Out of the box, this repository ships with a complete template configuration for **Software / AI / Web Engineering in Germany** (`Alex Morgan` in `candidate_profile.json`). To adapt it to **any other profession, seniority band, language profile, or country** (e.g., Data Science, Product Management, UX Design, Mechanical Engineering, Finance, UK/US/NL/CH/CA), update `candidate_profile.json`, `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`, `_agent_handoff/MASTER_RESUME_TEMPLATE.tex`, and the search queries/skill maps in `_agent_handoff/ats_keyword_check.py` and `_agent_handoff/harvest_all_portals.py`.

---

## 0. Mandatory Startup, `"run"` Trigger & 24/7 Continuous Synchronization Protocol

1. **One-Word `"run"` Trigger (Claude & Gemini — NEVER Stop Early!):**
   - Whenever the user types **`run`**, DO NOT ask unnecessary questions and DO NOT stop after 5–10 applications! Immediately execute the synchronized loop:
     1. Run `python _agent_handoff/sync_status.py` and read `candidate_profile.json` + `_agent_handoff/sweep_state.json`.
     2. **Drain `ready_to_submit_immediately`** in `sweep_state.json` first (any already-tailored, QA-verified Green Zone packages on disk).
     3. **Phase 1 — `< 24 Hours` Internet-Wide Sweep FIRST:** Harvest & apply to **every** `< 24h` Green Zone job across **ALL configured Job Portals + Search Engine ATS Dorks** (`Ashby, Greenhouse, Lever, Personio, Workable, Recruitee, SmartRecruiters, Teamtailor, JOIN, StepStone, Indeed, LinkedIn Guest API, XING, GermanTechJobs, Arbeitnow, BerlinStartupJobs, EnglishJobs.de, WeAreDevelopers, Make it in Germany, Arbeitsagentur BA, get-in-IT, Jobvector, Yourfirm, Jobware, stellenanzeigen.de, JobMESH, Zuhausejobs, Monster, Joblift, Talent.com, Glassdoor, Truffls, Welcome to the Jungle, Relocate.me, Himalayas, Wellfound`). Update `last_24h_sweep_at` ISO timestamps in `sweep_state.json`.
     4. **Phase 2 — Complete `14-Day` Backlog Sweep (`backlog_14d_all_complete == false`):** Pick up from the exact unfinished portals & page cursors in `sweep_state.json` (`portals[*].backlog_14d_completed == false`), tailoring and submitting every Green Zone match from the last 14 days up to today, and saving timestamps/cursors via `state_upd.py` after EVERY portal/batch so if tokens expire, the other agent (`Claude` <-> `Gemini`) resumes from the exact spot! Once all portals reach `backlog_14d_completed: true` (with `--screened >= 15`), `state_upd.py` sets `backlog_14d_all_complete: true` and `phase: "REALTIME_30M"`.
     5. **Phase 3 — Perpetual 30-Minute Real-Time Sweep (`REALTIME_30M`, 24/7 Until Stopped):** Every **30 minutes** (via Claude `/loop 30m` / `_agent_handoff/claude_24x7_watchdog.ps1` or Gemini `schedule` cron `"*/30 * * * *"`), sweep all portals + ATS feeds for newly posted jobs since `last_realtime_sweep_at` (`< 24h`), and tailor + apply immediately!
2. **Mandatory Dual Excel Logging (`Application_Tracker.xlsx` + `Manual_Apply_Queue.xlsx`):**
   - **Submitted jobs (`Applied`):** Log all 25 columns immediately in `Application_Tracker.xlsx` via `_agent_handoff/update_tracker_batch.py` (or `_agent_handoff/log_applied.py`).
   - **Blocked / CAPTCHA / Security / Manual-Action Green Zone jobs:** Never solve or bypass CAPTCHAs / Cloudflare Turnstile / hCaptcha / reCAPTCHA. Whenever a tailored Green Zone application cannot be submitted automatically (visual CAPTCHA, security block, pre-existing account password reset, ID/permit scan upload, or unconfirmed legal declaration), **IMMEDIATELY** upsert it into **`Manual_Apply_Queue.xlsx`** via `_agent_handoff/update_manual_queue.py` with the direct clickable apply URL, company name, role, blocker reason, language line, exact paths to the tailored Resume + Cover Letter PDFs, **`"copy_paste_pitch"` (Column Q: a plain, 100% human-written `<= 3 sentences` answer to *"What makes you a strong fit / Why us / Message to hiring team"* — zero AI clichés, zero em-dashes `—`, zero `"tailored"`)**, AND **`"copy_paste_answers"` (Column R: exact copy-paste answers to every form field & custom screening question on that page)** so the user can copy-paste and submit manually in 20 seconds!

---

## 1. JOB FRESHNESS PRIORITY & MULTI-PORTAL SEARCH (NEVER SINGLE-PORTAL!)

> **STRICT ANTI-SINGLE-PORTAL RULE:** NEVER camp on a single job board! Every search wave MUST harvest across **ALL 21+ Job Portals + Direct ATS Feeds** using `_agent_handoff/harvest_all_portals.py`, `_agent_handoff/public_portals.py`, `_agent_handoff/ats_poll.py`, `_agent_handoff/li_sweep.py`, and `_agent_handoff/ba_sweep.py`, paginating deeply across Pages 1–6+!

### A. Default 21+ Portals & Direct ATS Channels:
- **General & Commercial Job Boards:**
  1. **StepStone** (`stepstone.de` — `fdl=en`, `<24h` `ag=age_1` -> `<3d` `ag=age_3`, Pages 1–6+)
  2. **Indeed** (`de.indeed.com` — `<24h` `fromage=1` -> `<3d` `fromage=3`, Pages 1–6+, skipping sequential hex decoy cards)
  3. **stellenanzeigen.de** (`stellenanzeigen.de/suche/` — sorted by newest)
  4. **Yourfirm.de** (`yourfirm.de` — Mittelstand tech & SaaS hidden champions)
  5. **Jobware.de** (`jobware.de` — `jw_sort=datum`)
  6. **JobMESH.de** (`jobmesh.de` — `<24h` `d=1` -> `<3d` `d=3`)
- **Professional Networks:**
  7. **LinkedIn Jobs** (`li_sweep.py` + `li_jd.py` public guest API — `<24h` `f_TPR=r86400` -> `14d` `f_TPR=r1209600`)
  8. **XING Jobs** (`xing.com/jobs` — `sort=date`)
- **English-Friendly, Startup & Remote Portals:**
  9. **EnglishJobs.de** (`englishjobs.de` — Pages 1–5+)
  10. **Arbeitnow** (`arbeitnow.com/api/job-board-api`)
  11. **BerlinStartupJobs** (`berlinstartupjobs.com/engineering/`)
  12. **Zuhausejobs.com**, **Wellfound**, **startup.jobs**, **Welcome to the Jungle**, **Relocate.me**, **Himalayas**
  13. **Join.com** (`join.com`) & **Glassdoor** (`glassdoor.de`)
- **Official Public Portals:**
  14. **Make it in Germany** (`make-it-in-germany.com`)
  15. **Bundesagentur für Arbeit (`BA Jobsuche`)** (`ba_sweep.py` / `ba_api.py` REST API)
- **Specialized Tech & Early-Career Boards:**
  16. **get-in-IT.de** (`get-in-it.de/jobsuche`)
  17. **WeAreDevelopers** (`wearedevelopers.com/en/jobs`)
  18. **Jobvector.de** (`jobvector.de`)
  19. **Staufenbiel / Absolventa** & **devjobs.de**
  20. **Truffls.de** & **GermanTechJobs** (`germantechjobs.de/rss`)
- **Direct Multi-ATS Polling & Search Dorks:**
  21. `ats_poll.py` + `cdp_scripts/s_sp.js` across `jobs.ashbyhq.com`, `job-boards.greenhouse.io`, `jobs.lever.co`, `jobs.personio.de`, `apply.workable.com`, `*.recruitee.com`, `jobs.smartrecruiters.com`, and `*.teamtailor.com`.

### B. Strict Freshness Order (`< 24h` FIRST -> `48–64h` / `14d` SECOND)
1. **Tier 1 (`< 24 Hours` — Run FIRST):** Exhaust every `< 24h` Green Zone match across all portals first (`harvest_all_portals.py --window 24h`, `ats_poll.py - 1`, `li_sweep.py 24`, `ba_sweep.py 1`).
2. **Tier 2 (`48–64 Hours` & `14-Day Backlog`):** Expand only after `< 24h` matches are submitted. Record posting age and source portal in Column 25 (`Additional Notes`) of `Application_Tracker.xlsx`.

---

## 2. STRICT ZERO-REJECTION JOB FILTERING RULES (See `_agent_handoff/REJECTION_POSTMORTEM_AND_CONVERSION_RULES.md`)

> **MANDATORY PRE-READ:** Read `_agent_handoff/REJECTION_POSTMORTEM_AND_CONVERSION_RULES.md`! European HR typically counts `Working Student / Werkstudent` tenure at `0–50%`, so a candidate with ~2 yrs full-time + ~2 yrs Working Student experience is a **top-5% candidate on `0–4 YOE` roles** (`Junior`, `Associate`, `Graduate`, `Mid-Level`, and regular non-Senior Engineer/Developer roles) and gets auto-rejected on bare `Senior / Staff / Principal / Founding / Forward Deployed` requisitions.

### GREEN ZONE — Apply Immediately ONLY If ALL 4 Conditions Are Met:
1. **Spoken Language Fit (per `candidate_profile.json`):** For an `A2` German / fluent English profile, German must be **not required**, **"a plus / nice to have / von Vorteil / wünschenswert"**, or **A1–A2**. **Instant SKIP** if the JD requires `B1`, `B2`, `C1`, `"good German"`, `"very good German"`, `"fluent German"`, or `"gute Deutschkenntnisse"`.
2. **Strict `0–4 YOE` Seniority & Title Sweet Spot (Configurable via `targeting.yoe_max`):**
   - **APPLY TO:** `Junior`, `Working-Student-to-Full-Time / Graduate / Associate`, `Mid-Level`, and regular **non-Senior** roles in the candidate's target family asking **`0–3` or `2–4` years** (or no hard year gate).
   - **Parenthetical `(Senior)` Exception ONLY:** Allowed **only** if `(Senior)` is in parentheses **AND** the JD explicitly states **`2–4` / `3+` years** AND openness to mid-level profiles (`"allow_parenthetical_senior": true` in `spec.json`).
3. **Core Skill Match & Honest Fit Score `>= 82/100` (`gen_ats_analysis.py`):**
   - Verified against `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md` and `KNOWN` in `_agent_handoff/ats_keyword_check.py`.
4. **STRICT One Company = One Role Forever:**
   - Check **BOTH** `Application_Tracker.xlsx`, `Manual_Apply_Queue.xlsx`, AND all workspace `<Company>_<Role>/` folders BEFORE shortlisting or generating PDFs.
   - Never apply twice to the same job or to two roles at the same company (plus every company in `targeting.permanent_do_not_apply` and `employers` in `candidate_profile.json`).

### RED ZONE — Skip Immediately (Do NOT Shortlist & Do NOT Add to Excel):
1. **SKIP Mandatory `B1+` / `"Good"` / `"Fluent"` Local Language** (when above the candidate's configured level).
2. **SKIP Bare `"Senior"`, `"Staff"`, `"Lead"`, `"Principal"`, `"Architect"`, `"Engineering Manager"`, `"Founding Engineer"`, `"Forward Deployed Engineer"`, `"Solutions Engineer"`, `"Consultant / Berater"`, Defense/Clearance roles, and ANY JD requiring `5+ Years`!**
   - **ANTI-SHORTCUT PORTAL COMPLETION LAW:** **NEVER** mark a 14-day backlog portal `backlog_14d_completed: true` using `"aggregator"` / `"cross-covered"` excuses or shallow `<15`-card scrapes. Always update state via `python _agent_handoff/state_upd.py <portal> true "<cursor>" "<note>" --screened <N>` (`N >= 15` real scraped/screened cards).
3. **SKIP Unverified Core Stacks (ZERO Forgery):** Never shortlist roles whose mandatory primary stack is in `NEVER` (`ats_keyword_check.py`) or `forbidden_resume_terms` (`candidate_profile.json`).

---

## 3. HONEST 100-POINT ATS CALCULATION, PER-JOB PACKAGE & GOLD-STANDARD 1-PAGE RESUME

For **every** shortlisted Green Zone job, create folder `<Company>_<Role>/` at workspace root containing all **6 mandatory files** BEFORE submitting:

1. **`Job_Description.txt`:** Full JD text, company name, exact job title, location, work mode, posting age, and direct URL.
2. **`ATS_Analysis.md` (Honest 6-Category / 100-Point Rubric — Zero Keyword Forgery):**
   - **Keyword Table:** Categorize JD keywords into **Tier 1 (Critical Matched)**, **Tier 2 (Important Matched)**, and **Tier 3 (Unverified / Omitted — explicitly kept OUT of the CV for 100% honesty)**.
   - **100-Point Comparative Score Table (`Initial CV Score` -> `Tailored Resume Score`, minimum threshold `>= 82/100`):**
     1. `Required Technical Skills` (`30 pts`)
     2. `Relevant Professional Experience` (`25 pts`)
     3. `Relevant Responsibilities & Achievements` (`15 pts`)
     4. `Preferred / Supporting Skills` (`10 pts`)
     5. `Education & Qualifications` (`10 pts`)
     6. `ATS Structure & Readability` (`10 pts`)
   - **3-Perspective Review:** Critical check from (A) ATS Parser, (B) Technical Hiring Manager, and (C) HR Recruiter.
3. **`resume.tex` & `<Candidate>_Resume.pdf` (Built ONLY from `_agent_handoff/MASTER_RESUME_TEMPLATE.tex`):**
   - **Clean 4–5 Line `Summary` (`400–650 chars`):** Open with the **exact target JD title**, followed by 3–4 crisp sentences tailored to the JD's matched stack and domain.
   - **Full 1-Page Coverage (`>= 3,550 chars`, Strictly `1 Page`, Zero Empty Bottom Whitespace):**
     - Lead Work Experience with clear engineering/role titles so the PDF covers **95–98% of 1 A4 page**.
     - **Zero Employer Cross-Contamination (`_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`):** Attribute each framework, database, cloud tool, or AI pipeline strictly to the employer or project where it was genuinely used.
     - **7 Single-Occurrence Skill Rows:** Never duplicate skill row labels (`Languages:`, `Web and Frameworks:`, `Data and Messaging:`, `Cloud and DevOps:`, `AI Engineering:`, `Testing and Tools:`, `Spoken:`).
   - **Mandatory Pre-Upload QA Gate:** Compile with `tectonic` and run:
     `python _agent_handoff/validate_resume_pdf.py "<job_folder>/<Candidate>_Resume.pdf"` (must output `PASS QA: ... Strictly 1 full page`).
4. **`cover_letter.tex` & `<Candidate>_Cover_Letter.pdf` (100% Humanized Plain-Paragraph Standard — Zero Dashes, Zero Bullets, Zero AI Phrasing):**
   - Built from `_agent_handoff/MASTER_COVER_LETTER_TEMPLATE.tex` via `auto_tailor.py`: 4 short, natural, human-written paragraphs (`cl_hook` + 3 plain prose strings in `cl_bullets` — NO bold headings, NO `\begin{itemize}` bullet lists, NO `—` / `–` / `--` / ` - ` dashes, NO semicolons, NO AI clichés; natural contractions `"I'm"`, `"I've"`, `"I'd"`).
   - **NEVER include unsolicited salary in the cover letter** unless the JD explicitly requests salary expectations in the application text (`"include_salary_in_cl": true`).
   - **JD-Focused Stack Framing (Zero Framework Soup):** Set `"primary_stack"` in `spec.json` (`"react_nextjs"` | `"vue_nuxt"` | `"node_backend"` | `"fullstack_both"` | `"ai_llm"` | `"webgl_3d"`), write a custom `"summary"` focused on THAT JD's primary stack & domain, and pass custom `"bullet_rewrites"` & `"cl_bullets"` tied to the company's real product.

### 3A. MANDATORY ATS KEYWORD & PUNCTUATION MIRRORING
Rewriting only the Summary is NOT tailoring. Before EVERY submit:
1. **Run the keyword gate** (must show `MISSING: none` and `FORBIDDEN-IN-CV: none`):
   `python _agent_handoff/ats_keyword_check.py "<job_folder>/Job_Description.txt" "<job_folder>/<Candidate>_Resume.pdf"`
2. **Mirror the JD's EXACT wording AND EXACT punctuation/dots/hyphens/abbreviations (`React.js` != `React`!) for verified skills:**
   - Literal ATS tokenizers (`Lucene UAX#29` / Workday / Personio / Greenhouse / Teamtailor) treat `React.js` != `React` != `ReactJS`, `Node.js` != `NodeJS` != `Node`, `Next.js` != `NextJS`, `NestJS` != `Nest.js`, `PostgreSQL` != `Postgres`, `MongoDB` != `NoSQL`, `Kubernetes` != `K8s`, `TypeScript` != `TS`, `JavaScript` != `JS`, `Full-Stack` != `Full Stack` != `Fullstack`, `end-to-end` != `end to end` != `E2E`, and `Authorisation` != `Authorization`. `ats_keyword_check.py` + `auto_tailor.py` enforce exact token-boundary & punctuation matching across **every** occurrence in the JD.
3. **NEVER list skills the candidate does not know** (`NEVER` in `ats_keyword_check.py` / `forbidden_resume_terms` in `candidate_profile.json`). Keep them strictly in Tier 3 of `ATS_Analysis.md`.
4. **Fast build pipeline:** `python _agent_handoff/auto_tailor.py <spec.json>` compiles both PDFs and runs both QA gates; `python _agent_handoff/gen_ats_analysis.py <folder> "<Company>" "<Title>" "<note>"` writes `ATS_Analysis.md` and verifies `>= 82/100`.

---

## 4. CANDIDATE SOURCE OF TRUTH, FORM COMPLETENESS & ANTI-DUPLICATE-NAME PROTOCOL

- **Single Source of Truth:** Read all personal details, address, links, graduation/start dates, work-permit status, spoken language levels, and salary defaults from `candidate_profile.json` at repository root!
- **Mandatory Start-Date & Optional-Field Completeness Rule:** NEVER leave **`Earliest possible join date` / `Available from` / `Possible start date`** (or `Birthday`, `Phone`, `Desired salary`, `LinkedIn / GitHub / Portfolio`) input boxes blank on ANY web form (HRworks, Onlyfy, Personio, JOIN, Lever, Greenhouse, Ashby, Workable, Teamtailor, etc.), even when marked optional! Format dates cleanly for the target locale (`DD.MM.YYYY` on DE forms, `MM/DD/YYYY` on EN HRworks forms, `YYYY-MM-DD` on `input[type="date"]`). Use `_agent_handoff/cdp_scripts/hrworks_helper.js` for HRworks forms.
- **Anti-Duplicate-Name & Pre-Submit Readback Protocol:**
  1. **Upload Resume & Cover Letter PDFs FIRST**, then **wait `3000–4500 ms`** for Greenhouse / Lever / Personio / Ashby / Teamtailor / Workable CV auto-parsing to finish before setting form fields (so CV parsing never overwrites relocation radios or duplicates names like `AlexAlex`)!
  2. Use `clear_and_set_verified()` from `_agent_handoff/headless_browser.py` (never `.type()` onto non-empty inputs!).
  3. **Pre-Submit DOM Readback Assertion:** Right BEFORE clicking `Submit`, read back live DOM `.value` on `firstName`, `lastName`, `startDate/joinDate`, `salary`, and required checkboxes/radios to assert exact match against `candidate_profile.json`.
  4. Capture a silent confirmation screenshot (`confirmation.png`) inside `<Company>_<Role>/`, then **immediately** log all 25 columns in `Application_Tracker.xlsx`!
