# Persistent Autonomous Job Search & Application Memory (`AGENT_PLAYBOOK_MEMORY.md`)

## 1. Candidate Source of Truth (STRICT — ZERO FORGERY)
All candidate personal data, links, graduation/availability dates, work authorization, spoken languages, target roles, and employer boundaries live in **`candidate_profile.json`** (mirrored in `_agent_handoff/candidate_profile.md` and `_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`).

- **Default Template Profile (replace with your own during onboarding):**
  - **Full Name:** `Alex Morgan` (`First Name`: `Alex` | `Last Name`: `Morgan`)
  - **Location:** `Berlin, Germany` (open to relocation/hybrid/remote across target country)
  - **Email:** `alex.morgan.dev@example.com` | **Phone:** `+49 170 0000000`
  - **Official Header Links (ALL 3 required on every Resume & Cover Letter):**
    - **LinkedIn:** `https://linkedin.com/in/alex-morgan-example`
    - **GitHub:** `https://github.com/alex-morgan-example`
    - **Portfolio:** `https://alex-morgan-dev.example.com`
  - **Expected Gross Annual Salary:** `EUR 60,000 - 70,000` (`65000` default single-number input; omit from cover letter unless requested)
  - **Available Start Date:** `01.12.2026`
  - **Spoken Languages:** `English (fluent), German (A2, actively improving)` — NEVER fabricate higher language fluency and NEVER inject city/commute notes inside the `Spoken:` line!

## 2. Master Resume Standard (`_agent_handoff/MASTER_RESUME_TEMPLATE.tex` & `SAMPLE_GOLDEN_RESUME.pdf`)
- **ALWAYS** generate `resume.tex` from `_agent_handoff/MASTER_RESUME_TEMPLATE.tex` via `_agent_handoff/auto_tailor.py`:
  1. **Summary (`4–5 full lines`, `400–650 chars`):** Open with the exact target JD title, followed by 3–4 substantive sentences focused on the JD's primary stack and domain.
  2. **Skills (Strictly 7 single-occurrence categories — NEVER repeat `Spoken:` and NEVER put `Education:` inside Skills):**
     - `Languages:`
     - `Web and Frameworks:`
     - `Data and Messaging:`
     - `Cloud and DevOps:`
     - `AI Engineering:`
     - `Testing and Tools:`
     - `Spoken:`
  3. **Work Experience, Thesis, Projects, Certifications:** Keep multi-line achievement bullets truthful and intact within each employer's verified stack (`_agent_handoff/CURRENT_COMPANY_TECH_STACK.md`) so the compiled PDF fills **95–98% of 1 A4 page** (`>= 3,550 chars`) with zero empty gap at the bottom and zero spillover onto page 2.
  4. **Mandatory Pre-Upload Validator:** Run `python _agent_handoff/validate_resume_pdf.py <Resume.pdf>` AND `python _agent_handoff/ats_keyword_check.py <Job_Description.txt> <Resume.pdf>` before every upload.

## 3. Priority Role Archetypes (`0–4 YOE` Default Template)
1. **Full-Stack Engineer / Developer (`TypeScript + Node.js + Vue.js 3 / React / Next.js`)** — B2B SaaS, Billing/Metering, Cloud & Event-Driven Platforms.
2. **Frontend Engineer (`Vue 3 / Nuxt 3 / React / Next.js / TypeScript`)** — Composition API, Pinia, Vite, Tailwind CSS, design systems, Vitest, Playwright.
3. **Backend Engineer (`Node.js / TypeScript`, Microservices, SQL/MongoDB, Redis)** — Express.js / NestJS, REST/OpenAPI, Zod, MongoDB aggregations, Redis Streams, GCP Pub/Sub.
4. **AI / Applied LLM Engineer (`TypeScript / Full-Stack AI`)** — LangGraph, LangChain, RAG + vector search, MCP servers, AI coding agents, LLM evals.
5. **3D Web / Interactive Visualization Engineer (`React 19 + TypeScript + Three.js + react-three-fiber + @react-three/drei + WebGL`)** — highlight 3D WebGL skills in `Summary` & `Web and Frameworks:` and expand the **Master's Thesis** section while staying strictly 1 page.

## 4. STRICT Hard Disqualification Rules (Do NOT Shortlist & Do NOT Add to Excel)
1. **NO Mandatory `B1 / B2 / C1 / C2` German Roles** (for an `A2` profile): Skip any job requiring fluent/conversational/B1+ German (`German is a plus / von Vorteil` is GREEN even on German-written JDs).
2. **NO `5+ Years` or Bare `Senior / Staff / Principal / Lead / Founding` Roles:** Target `0–4 YOE` Junior, Graduate, Associate, Mid-Level, and regular non-Senior roles.
3. **NO Unverified Core Stacks:** Skip roles whose mandatory backend/core stack is in `NEVER` (`Java/Spring`, `C#/.NET`, `Go`, `Rust`, `C++`, `PHP`, `Ruby`, `Scala`, `Mobile-only`, `SAP/Salesforce/Mendix`).
4. **NEVER Apply Twice to the Same Job OR Same Company (`1 Company = 1 Role MAX, Forever`):** Always verify against `Application_Tracker.xlsx`, `Manual_Apply_Queue.xlsx`, `candidate_profile.json`, and workspace folders first.
