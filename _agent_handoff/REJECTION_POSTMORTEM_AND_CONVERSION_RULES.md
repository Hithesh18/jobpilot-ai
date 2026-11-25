# Forensic Postmortem of Historical Rejections vs. Interview Conversions & Zero-Rejection Rules

> **Purpose:** Empirical calibration reference shared by **Claude Code** and **Gemini (Antigravity)**. Derived from an audit of ~300 real-world European/German tech applications (`39` early-stage rejections vs. multiple technical-interview & coding-challenge conversions) to eliminate false-positive applications and maximize interview conversion rate.

---

## 1. Executive Finding: Why High Keyword Overlap Still Got Rejected in Uncalibrated Runs

Comparing raw keyword overlap against actual recruiter outcomes exposed **four systemic failure modes** that JobPilot AI now blocks programmatically:

1. **Keyword Overlap Without Recruiter Knockout Gates:**
   - Early uncalibrated packages achieved high keyword coverage on paper while ignoring hard human-recruiter knockouts (`German B2/C1` required, `6–8+ YOE Senior/Principal` tenure bar, `24/7 Founding Engineer` expectation, `Defense security clearance`, or `Java/Go/Airflow` primary stacks).
2. **How European / German HR Calculates Post-Graduation Experience (The `Werkstudent` Discount):**
   - Recruiters in DACH/EU typically count `Working Student (Werkstudent)` or internship tenure at **0–50%** toward full-time `Berufserfahrung`.
   - **Result:** A candidate with ~2 years full-time + ~2 years Working Student experience + an M.Sc. ranks in the **top 5% of applicants** on **`Junior`, `Associate`, `Graduate`, `Mid-Level`, and regular non-Senior `Full Stack / Frontend / Backend / Web / AI Engineer` (`0–4 YOE`)** roles. On bare **`Senior` (`5+ yrs`), `Staff`, `Principal`, `Founding`, or `Forward Deployed`** requisitions, HR screens out current `Working Student` titles in seconds regardless of stack overlap.
3. **Framework Soup vs. JD-Focused Stack Framing:**
   - Merely swapping the job title in line 1 of the Summary while dumping competing frameworks (`Vue.js 3, React, Next.js, Angular`) in random order weakens signal.
   - **Fix (`detect_primary_stack` in `auto_tailor.py`):** If a company asks for **React + Next.js**, lead the Summary and `Web and Frameworks:` row with **`TypeScript, React, Next.js, Node.js, NestJS`** and highlight real React/Next.js achievements first. If the JD asks for **Vue 3 + Pinia**, lead with **`TypeScript, Vue.js 3 (Composition API, Pinia), Vite, Tailwind CSS, Node.js`**.
4. **AI-Sounding Cover Letters & Unsolicited Salary Anchors:**
   - Generic templates stuffed with em-dashes (`—`), bulleted clichés (`"passionate"`, `"thrilled"`, `"seamlessly"`, `"at the intersection of"`), or unrequested salary demands underperform plain, human-written 4-paragraph cover letters tied to the company's actual product.

---

## 2. Quantitative Breakdown of Historical Rejection Archetypes (`N = 39`)

| Root Rejection Category | Share of Rejections | Why Uncalibrated Applications Failed | Programmatic Gate Now Enforced |
|---|---:|---|---|
| **A. Senior / Staff / Principal / Founding Tenure Gate (`5–10+ YOE`)** | **46.2%** | Stack matched, but HR filtered out `0–4 YOE` / current `Working Student` profiles on `Senior/Staff/Principal/Founding` requisitions. | `RED_TITLE` + `HARD_YOE_KO` hard-block bare `Senior`, `Staff`, `Principal`, `Lead`, `Founding`, and `5+ YOE` gates. |
| **B. Explicit or Implied `B1/B2/C1` Local-Language Requirement** | **28.2%** | Even with a 90%+ stack match, `A2` German is an automatic knockout when a JD requires `"good/fluent/B2/C1 German"` or `"Deutsch in Wort und Schrift"`. | `german_requirement()` + `GERMAN_KO` (tested across 48 real German/English JD edge cases in `test_german_requirement.py`). |
| **C. Primary Core Stack / Domain / Clearance Mismatch** | **15.4%** | Secondary tools (`Docker, SQL, React`) matched while the primary hiring need was `Java/Spring`, `Go`, `Airflow/dbt Data Lake`, `Mendix`, or `NATO/Ü2 clearance`. | `NEVER` gate + `gen_ats_analysis.py` heavy core-language penalty (`-7 pts` per missing mandatory core language) + `CLEARANCE_KO`. |
| **D. Form Autofill / Duplicate-Apply / Untailored Submissions** | **7.7%** | Applying to two roles at the same company on the same day, or CV parser race conditions duplicating first names (`AlexAlex`). | Strict `1 Company = 1 Role Forever` (`is_dup_company`) + post-upload wait + `clear_and_set_verified()` + pre-submit DOM readback assertion. |
| **E. External Hiring Budget Freeze** | **2.6%** | Role paused until next quarter (candidate retained in recruiter talent pool — not a profile mismatch). | Tracked cleanly via `sync_gmail_updates.py`. |

### What Converted Consistently (Our True North)
- **`(Junior)` / Regular `Full Stack Developer` & `Product Engineer` (`0–4 YOE`, English-speaking teams):**
  - Exact `TypeScript, React/Next.js or Vue 3, Node.js/NestJS, SQL/MongoDB, Redis, Docker` match + single-column 1-page PDF + plain, human-written cover letter naming a real product workflow + zero unsolicited salary.

---

## 3. Mandatory Conversion Rules Enforced Across All Sessions

1. **Language Requirement Nuance (`test_german_requirement.py`):**
   - A German-written JD is **NOT** an automatic skip! Read the actual language requirement: SKIP only if German is required at `B1+` / `"gute / sehr gute / fließende Deutschkenntnisse"` / `"Deutsch in Wort und Schrift"`. If German is `"von Vorteil / wünschenswert / a plus"` or unmentioned, the role is **GREEN**.
2. **Strict Seniority & YOE Calibration (`candidate_profile.json`):**
   - Stick strictly within the candidate's true full-time equivalent experience band (`0–4 YOE` in the default template). Allow parenthetical `(Senior)` **only** when the JD explicitly invites `2–4` / `3+` YOE and mid-level candidates (`allow_parenthetical_senior: true`).
3. **Coherent, Truthful Employer Attribution (`CURRENT_COMPANY_TECH_STACK.md`):**
   - Never graft JD buzzwords onto unrelated past employers or projects, and never cross-contaminate tech stacks across companies.
4. **100% Humanized Cover Letters & Emails (`validate_resume_pdf.py` + `gmail_helper.js`):**
   - Zero dashes (`—`, `–`, `--`, ` - `), zero bullet lists, zero bold inline headings, zero semicolons, and zero AI clichés (`"tailored"`, `"customized"`, `"passionate"`, `"thrilled"`, `"leverage"`, `"synergy"`, `"seamlessly"`).
5. **Exact Punctuation, Dot, Hyphen & Abbreviation Mirroring (`ats_keyword_check.py`):**
   - Literal ATS filters (`Lucene UAX#29`) treat `React.js` != `React` != `ReactJS`, `Node.js` != `NodeJS` != `Node`, `PostgreSQL` != `Postgres`, `Kubernetes` != `K8s`, `Full-Stack` != `Fullstack` != `Full Stack`, and `end-to-end` != `end to end`. Always mirror every verified JD spelling verbatim!
6. **Continuous Post-Rejection Fine-Tuning (`sync_gmail_updates.py`):**
   - Periodically run `python _agent_handoff/sync_gmail_updates.py` to sync recruiter replies from Gmail into `Application_Tracker.xlsx`. Whenever a new rejection pattern emerges (e.g., a subtle consulting language expectation or niche domain mismatch), add the pattern directly to `RED_TITLE` / `GERMAN_KO` / `AGENTS.md` so neither Claude nor Gemini ever repeats it.
