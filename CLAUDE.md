# Claude Code / VS Code Instructions (`jobpilot-ai`)

@AGENTS.md

## Mandatory Pre-Read Before Every Session
1. Read `candidate_profile.json` (candidate identity, links, availability, target roles, language rules, and permanent do-not-apply list).
2. Read `_agent_handoff/REJECTION_POSTMORTEM_AND_CONVERSION_RULES.md` (forensic rejection audit & conversion rules).
3. Read `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md` (strict per-employer verified stack boundaries).
4. Run `python _agent_handoff/sync_status.py` and inspect `_agent_handoff/sweep_state.json`.
5. **Silent Background Browser Execution Only:**
   - Persistent Chrome Background Tabs (`Target.createTarget({ background: true })` + `Emulation.setFocusEmulationEnabled({ enabled: true })`): `http://127.0.0.1:9333` (`powershell -ExecutionPolicy Bypass -File "_agent_handoff/cdp_scripts/run.ps1" -Script "<script.js>"` or POST `{"scriptPath": "..."}` to `http://127.0.0.1:9333`). If `http://127.0.0.1:9333` is not running yet, run `python _agent_handoff/bridge_ensure.py` or `node _agent_handoff/cdp_bridge.js` in background first.

---

## Non-Negotiable Zero-Rejection Targeting & Tailoring Rules

1. **STRICT `0–4 YOE` Sweet Spot ONLY (Configurable in `candidate_profile.json`):**
   - **ONLY apply to:** `Junior`, `Working-Student-to-Full-Time / Graduate / Associate`, `Mid-Level`, and regular **non-Senior** roles in the candidate's target family asking **`0–3` or `2–4` years** (only allow `(Senior)` in parentheses if the JD explicitly states **`2–4` / `3+` years** AND openness to mid-level profiles, passing `"allow_parenthetical_senior": true`).
   - **HARD-BLOCK:** Bare `Senior`, `Staff`, `Principal`, `Lead`, `Architect`, `Manager`, `Founding Engineer`, `Forward Deployed / Solutions Engineer`, `Consultant / Berater`, `Data Platform / Data Lake` (unless configured), `MLOps / SRE`, Defense/Clearance roles, ANY `5+ YOE` requirement, and ANY local-language requirement above the candidate's configured level!

2. **Custom 1-Page CV & 100% Humanized Plain-Paragraph Cover Letter (`auto_tailor.py` + `gen_ats_analysis.py`):**
   - **NEVER produce generic copy-paste CVs or boilerplate cover letters!** For every Green Zone role, pass a rich per-job `spec.json` into `python _agent_handoff/auto_tailor.py <spec.json>` containing:
     - `"primary_stack"`: `"react_nextjs"` | `"vue_nuxt"` | `"node_backend"` | `"fullstack_both"` | `"ai_llm"` | `"webgl_3d"` (matching the JD's actual stack — NEVER dump competing frameworks into sentence 1!).
     - `"summary"`: Custom 4–5 line (`400–650` chars) Summary starting with the exact JD title and highlighting ONLY genuinely overlapping verified stack & real engineering work — **mirroring the JD's EXACT punctuation, dots, hyphens & abbreviations** (`React.js` vs `React` vs `ReactJS`, `Node.js` vs `NodeJS` vs `Node`, `Next.js` vs `NextJS`, `Postgres` vs `PostgreSQL`, `NoSQL` vs `MongoDB`, `K8s` vs `Kubernetes`, `JS/TS` vs `JavaScript/TypeScript`, `Full-Stack` vs `Fullstack` vs `Full Stack`, `end-to-end` vs `end to end`).
     - **STRICT COHERENT REAL-EXPERIENCE RULE:** Every sentence MUST make 100% logical & factual sense against `candidate_profile.json`, `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`, and `_agent_handoff/MASTER_RESUME_TEMPLATE.tex` — zero buzzword grafting and zero employer cross-contamination!
     - `"bullet_rewrites"`: Reword 1–3 bullets (within truthful employer stack boundaries!) so JD priorities appear in real achievement bullets.
     - `"cl_hook"` + `"cl_bullets"` (**100% HUMANIZED COVER LETTER RULE**): Pass 3 plain, natural human prose paragraphs. **STRICTLY FORBIDDEN IN COVER LETTERS:** ANY dashes (`—`, `–`, `--`, `---`, or spaced ` - `), bullet lists (`•` / `\begin{itemize}`), bold inline headings, semicolons (`;`), and AI clichés (`"passionate"`, `"thrilled"`, `"excited"`, `"delighted"`, `"leverage"`, `"synergy"`, `"seamlessly"`, `"cutting-edge"`, `"at the intersection of"`, `"thrive in"`, `"aligns directly"`, `"uniquely positioned"`, `"I am writing to express"`, `"tailored"`, `"customized"`). Omit salary unless the JD explicitly asks for salary in the cover letter (`"include_salary_in_cl": true`).
   - Run `python _agent_handoff/gen_ats_analysis.py "<folder>" "<Company>" "<Title>" "<portal + posting age>"` — must output `APPLY (GREEN ZONE)` (`>= 82/100`).

3. **Execution Order & Synchronized State (`sweep_state.json` + Dual Excel):**
   - **Phase 1 (`< 24h` Sweep FIRST):** Run `ats_poll.py - 1`, `cdp_scripts/s_sp.js` (`date: "d"`) + `screen_google.py`, `harvest_all_portals.py --window 24h` + `screen_harvest.py`, `public_portals.py`, `li_sweep.py 24`, and `ba_sweep.py 1`. Tailor & apply to every `<24h` Green Zone match immediately!
   - **Phase 2 (`14-Day` Open Portals in `sweep_state.json`):** Work systematically through each `backlog_14d_completed == false` portal, updating cursors via `state_upd.py <portal> true "<cursor>" "<note>" --screened <N>` (`N >= 15` real cards, zero `"cross-covered"` shortcuts!).
   - **Phase 3 (`/loop 30m` Real-Time Sweep):** Once all 14-day portals pass verification, run 30-minute real-time sweeps (`/loop 30m` or `realtime_iter.sh`) for newly posted `<24h` roles.
   - **Mandatory Form Completeness, Post-Upload Readback & Proof:**
     - Upload Resume + Cover Letter FIRST, wait `3.5–4.5s` for CV auto-parsers to finish, and fill/toggle form fields AFTER!
     - NEVER leave **`Earliest possible join date` / `Possible start date` / `Available from`** or optional fields (`Birthday`, `Phone`, `Salary`, `LinkedIn / GitHub / Portfolio`) blank!
     - Run a **hard pre-submit DOM readback assertion** on `firstName`, `lastName`, `startDate/joinDate`, `salary`, and all radio/checkbox answers BEFORE clicking `Submit`, save `confirmation.png` inside the job folder, log `Applied` jobs immediately via `update_tracker_batch.py` / `log_applied.py`, and log CAPTCHA/security-gated Green Zone packages immediately to `Manual_Apply_Queue.xlsx` via `update_manual_queue.py` with both `"copy_paste_pitch"` and `"copy_paste_answers"`.
   - **Daily Summary Table Rule:** Whenever asked for today's applied jobs or summary, ALWAYS show the exact **total count applied today** at the top followed by a Markdown table with columns: **`#` | `App ID` | `Company` | `Role` | `Tech Stack` | `ATS Score` | `ATS / Portal`**.
   - **Gmail & Portal Message Boxes:** Always use `_agent_handoff/cdp_scripts/gmail_helper.js` (`buildHumanEmailBody` + `sendCleanApplicationEmail`) for email applications (`<= 120 words`, zero bullet lists, zero em-dashes `—`, zero `"tailored"` or AI clichés).
