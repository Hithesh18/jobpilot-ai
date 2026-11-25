r"""
Zero-Rejection Package Builder (`_agent_handoff/auto_tailor.py`)
Shared by Claude Code & Gemini Antigravity — Cross-Platform Native Python + Tectonic.

Enforces ALL lessons from `_agent_handoff/REJECTION_POSTMORTEM_AND_CONVERSION_RULES.md` + Exact Punctuation Gate:
  1. HARD PRE-BUILD DEALBREAKER GATE (`exit 2` before compiling if Red Zone):
     - Blocks bare `Senior`, `Staff`, `Principal`, `Lead`, `Head`, `Director`, `Architect`, `Manager`,
       `Founding`, `Forward Deployed`, `Solutions Engineer`, `Consultant/Berater`, `Data Engineer/Platform/Lake`,
       `MLOps/SRE`, and Defense/Clearance roles.
     - `(Senior)` in parentheses is allowed ONLY if `allow_parenthetical_senior: true` AND JD asks <=4 YOE + mid-level openness.
     - Blocks German `B1/B2/C1/C2`, `"good/very good/fluent German"` (German-WRITTEN JDs are fine if German is not required).
     - Blocks hard `5+ / 6+ / 7+ / 8+ years` requirements.
  2. JD-FOCUSED STACK FRAMING (Zero Framework Soup):
     - Auto-detects (or uses `primary_stack`: `react_nextjs` | `vue_nuxt` | `node_backend` | `fullstack_both` | `ai_llm` | `webgl_3d`).
     - Leads Summary & Skills with THAT JD's primary stack and places key tools inside truthful achievement bullets.
  3. EXACT PUNCTUATION, DOT, HYPHEN & ABBREVIATION MIRRORING (`React.js` != `React`):
     - Uses `ats_keyword_check.evaluate_jd_against_pdf` directly (single source of truth).
     - Upgrades skill tokens & prose compounds IN-PLACE (`React` -> `React.js`, `Node.js` -> `Node.js (Node)` / `NodeJS`,
       `PostgreSQL` -> `PostgreSQL (Postgres)`, `Kubernetes` -> `Kubernetes (K8s)`, `MongoDB` -> `MongoDB (NoSQL)`,
       `TypeScript` -> `TypeScript (TS)`, `JavaScript` -> `JavaScript (JS)`, `end to end` -> `end-to-end`,
       `full-stack` / `fullstack`) so literal ATS filters NEVER reject over a dot, hyphen, or acronym while keeping
       the 1-page CV 100% natural for human engineers.
  4. 100% HUMANIZED PLAIN-PARAGRAPH COVER LETTER:
     - Specific product hook + 3 plain human paragraphs + clean closing (zero dashes, zero bullets, zero AI clichés, no unsolicited salary).

Usage:
  python _agent_handoff/auto_tailor.py <spec.json>
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import ats_keyword_check as akc  # noqa: E402
import pypdf  # noqa: E402
from profile_loader import (  # noqa: E402
    cover_letter_pdf_filename,
    get_python_exe,
    get_tectonic_exe,
    load_profile,
    resume_pdf_filename,
)

PROF = load_profile()
CAND = PROF.get("candidate", {})
EMPS = PROF.get("employers", {})
ANCH = PROF.get("experience_anchors", {})

CUR_EMP = EMPS.get("current", {}).get("name", "Northstar Cloud GmbH")
CUR_EMP_HDR = EMPS.get("current", {}).get("header_tex", "Northstar Cloud GmbH, Berlin")
CUR_CITY = EMPS.get("current", {}).get("city", "Berlin")
AI_BOT_NAME = EMPS.get("current", {}).get("ai_feature_name", "AtlasCopilot")
PREV1_EMP = EMPS.get("previous_1", {}).get("name", "PulseEvent Technologies")
PREV1_EMP_HDR = EMPS.get("previous_1", {}).get("header_tex", "PulseEvent Technologies, Berlin")
PREV2_EMP = EMPS.get("previous_2", {}).get("name", "CoreTel Systems")
EDU_DEG = CAND.get("education", {}).get("current_degree", "M.Sc. in Computer Science")
EDU_UNI = CAND.get("education", {}).get("current_university", "Technical University of Berlin")
EDU_GRAD = CAND.get("education", {}).get("graduation_month_year", "November 2026")
START_PROSE = CAND.get("availability", {}).get("earliest_start_prose", "1 December 2026")
PROJ_URL = CAND.get("links", {}).get("flagship_project_url", "https://kiezhub.example.org")
PROJ_DISP = CAND.get("links", {}).get("flagship_project_display", "kiezhub.example.org")

TECT = get_tectonic_exe()
PY = get_python_exe()
RES = resume_pdf_filename(PROF)
CLP = cover_letter_pdf_filename(PROF)

# Exact template anchor lines in MASTER_RESUME_TEMPLATE.tex (customizable in candidate_profile.json)
S1 = ANCH.get(
    "s1",
    "Build and release multi-tenant SaaS features end to end with TypeScript, Node.js, Express.js, Vue.js 3, PostgreSQL, and MongoDB.",
)
S4 = ANCH.get(
    "s4",
    "Hardened tenant-boundary enforcement across subscription endpoints with strict JWT/OAuth 2.0 and RBAC checks, removing permissive token fallbacks and adding Supertest regression suites.",
)
M1 = ANCH.get(
    "m1",
    "Built attendee registration and live-ticketing features end to end with React, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models.",
)
T1 = ANCH.get(
    "t1",
    "Developed customer-facing enterprise billing and reporting workflows using React, Angular, JavaScript, and SQL.",
)
T2 = ANCH.get(
    "t2",
    "Owned the Account Reconciliation module end to end and built reusable React and backend components that improved dashboard load times.",
)
TH = ANCH.get(
    "th",
    "an interactive 3D web visualization client (React 19, TypeScript, react-three-fiber) with real-time WebSocket camera synchronization and level-of-detail GLTF scene streaming across four urban models.",
)
P1 = ANCH.get(
    "p1",
    "Open-source neighborhood resource-sharing and booking web app built with React 18, TypeScript, Vite, Node.js, Express, and MongoDB Atlas, featuring JWT role-based moderation and OTP email verification.",
)

HARD_BLOCK_TITLE = re.compile(
    r"\bstaff\b|\bprincipal\b|\blead\b|\bteam.?lead\b|\bhead of\b|\bdirector\b|\bvp\b|\barchitect\b|"
    r"\bengineering manager\b|\bfounding\b|\bco-?founder\b|\bforward deployed\b|\bsolutions? engineer\b|"
    r"\bconsultant\b|\bberater\b|\bdata platform\b|\bdata engineer\b|\bdata lake\b|\bmlops\b|\bsre\b|"
    r"\bwerkstudent|\bworking student|\bintern\b|\binternship|\bpraktik",
    re.I,
)
GERMAN_KO = re.compile(
    r"(?:good|very good|excellent|strong|solid|fluent|business[- ]fluent|proficient|professional|conversational|advanced)\s+(?:written\s+and\s+spoken\s+|command\s+of\s+|knowledge\s+of\s+)?german|"
    r"german\s*(?:language\s*)?(?:level|skills?|proficiency|fluency)?\s*(?:at\s+)?[:(\-]?\s*(?:b1|b2|c1|c2|fluent|native)\b|"
    r"verhandlungssicher|flie(?:ß|ss)end(?:e|es|en)?\s+deutsch|deutsch\s*\(?\s*(?:flie(?:ß|ss)end|verhandlungssicher|muttersprach)|"
    r"(?:gute|gutes|guten|guter|sehr gute|sehr gutes|sehr guten|ausgezeichnete|exzellente|fundierte|sichere|gute bis sehr gute)\s+deutsch|"
    r"deutsch(?:kenntnisse)?\s*(?:auf\s*|mind\.?\s*|mindestens\s*)?(?:niveau\s*)?\(?\s*(?:b1|b2|c1|c2)\b|"
    r"\b(?:good|very good|excellent|strong|solid|fluent)\b[^.]{0,50}\bin\s+german\b|"
    r"\b(?:fluent|fluency|proficient|proficiency)\s+in\s+(?:both\s+)?(?:english\s+(?:and|&)\s+)?german\b|\bgerman\s+(?:and|&)\s+english\s+(?:fluency|skills)?\s*(?:are\s+)?(?:required|mandatory|essential|a must)|"
    r"(?:kommuniz\w*|kommunikation\w*|sprichst|sprechen|bewegst\s+dich|austausch|verständigen)[^.]{0,60}\b(?:auf|in)\s+deutsch|"
    r"deutsch\w*[^.]{0,30}\b(?:b1|b2|c1|c2)\b|\b(?:b1|b2|c1|c2)[- ]deutsch|\b(?:b1|b2|c1|c2)[- ]+german\b|"
    r"\bdeutschkenntnisse\s+(?:erforderlich|zwingend|vorausgesetzt|unabdingbar)\b|"
    r"\b(?:b1|b2|c1|c2)[- ]?(?:niveau\s+)?(?:ist\s+)?ausreichend|"
    r"\bsehr\s+gut\s+deutsch|\bdeutsch\w*[^.]{0,40}\b(?:nutzt|sprichst|beherrschst|sprechen)\s+(?:du|sie)\s+(?:flie(?:ß|ss)end|sicher|verhandlungssicher)|"
    r"\bdeutsch\s+und\s+englisch(?:kenntnisse)?\s+(?:(?:sehr\s+gut|gut|fließend|fliessend|verhandlungssicher)\s+)?in\s+wort\s+und\s+schrift|\bdeutsch\s*\(\s*(?:sehr\s+gut|gut|fließend|fliessend|verhandlungssicher|muttersprach\w*|c1|c2|b2)|\bdeutsch\w*\s+(?:beherrschen|sprechen)\s+sie\s+(?:flie(?:ß|ss)end|sicher|verhandlungssicher)|"
    r"\b(?:beherrschst|beherrschen|sprichst|sprechen)\s+(?:du\s+|sie\s+)?die\s+deutsche\s+sprache\s+(?:flie(?:ß|ss)end|sicher|verhandlungssicher|sehr\s+gut)|\bdeutsche\s+sprache\s+(?:flie(?:ß|ss)end|verhandlungssicher)|"
    r"\bdeutsch\w*\s+(?:auf|mit)\s+(?:muttersprachlichem|verhandlungssicherem|sehr\s+gutem|gutem|fließendem|fliessendem|c1|c2|b2)[\s-]*niveau|\bsprichst\s+deutsch\s+(?:fließend|fliessend|sehr\s+gut|gut|verhandlungssicher)|"
    r"\bdeutsch\w*\s+(?:mind(?:\.|estens)?\s+)?(?:auf\s+)?(?:b2|c1|c2)[\s-]*niveau|\bdeutsch\w*\s+auf\s+verhandlungssicherem\s+niveau\s+sowie|"
    r"\b(?:flie(?:ß|ss)end\w*|ausgezeichnet\w*|exzellent\w*|sehr\s+gut\w*|verhandlungssicher\w*)\s+(?:\w+\s+){0,4}(?:kommunikations\w*|sprachkenntnisse|kenntnisse)\s+in\s+(?:englisch\s+und\s+deutsch|deutsch\s+und\s+englisch)|"
    r"\b(?:sehr\s+)?gute\w*\s+(?:sprach)?kenntnisse\s+in\s+(?:deutsch|der\s+deutschen\s+sprache)|"
    r"\b(?:mindestens\s+|min\.\s*)?deutsch\w*\s+(?:auf|mit)\s+(?:mindestens\s+)?(?:dem\s+)?(?:b1|b2|c1|c2)[\s-]*niveau|"
    r"\b(?:good|strong|very\s+good|excellent|fluent|solid)\s+(?:\w+\s+){0,3}(?:skills|knowledge|command)\s+in\s+(?:both\s+)?(?:english\s+and\s+german|german\s+and\s+english)\b|"
    r"deutsch(?:kenntnisse)?\s+in\s+wort\s+und\s+schrift|"
    r"\bdeutsch(?:kenntnisse)?\s+(?:sind|ist)\s+(?:sehr\s+gut|gut|flie(?:ß|ss)end|verhandlungssicher|erforderlich|zwingend|voraussetzung|unabdingbar)|"
    r"\bdeutsch(?:\s+und\s+englisch)?\s+(?:sehr\s+gut|gut|flie(?:ß|ss)end|sicher|verhandlungssicher)\s+beherrsch\w*|\bdeutsch\w*[^.!?\n]{0,65}\b(?:mind(?:estens|\.)?\s+)?(?:auf\s+)?(?:b1|b2|c1|c2)[\s-]*niveau",
    re.I,
)
HARD_YOE_KO = re.compile(
    r"\b(?:[5-9]|1\d)\+\s*(?:years|yrs)\s+(?:of\s+)?(?:professional\s+|full[- ]time\s+|relevant\s+|hands[- ]on\s+)?"
    r"(?:experience|software|engineering|development|frontend|front-end|backend|back-end|full[- ]?stack)",
    re.I,
)
CLEARANCE_KO = re.compile(r"sicherheitsüberprüfung|\bü2\b|\bü3\b|nato clearance|security clearance required", re.I)
HELPDESK_KO = re.compile(r"\bservicedesk\b|\bhelpdesk\b|\b1st[- ]level[- ]support\b|\bpower\s+platform\b|\bpower\s*apps\b", re.I)
ANTI_AI_KO = re.compile(
    r"\b(?:without|no|avoid\w*|ohne)\s+(?:using\s+|any\s+)?(?:ai(?:-assisted|-based)?|artificial intelligence|ki(?:-gestützte|-basierte|-tools)?|coding\s+(?:agents?|assistants?))\b",
    re.I,
)


def tex_esc(s: str) -> str:
    return (
        s.replace("\\", "")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("$", r"\$")
    )


def clean_title(t: str) -> str:
    m_gender = re.search(
        r"\s*[\(\[]\s*(?:m|w|f|d|x|h|u|a|n|all genders?|gn|mwd|fmd)(?:\s*[/|,]\s*(?:m|w|f|d|x|h|u|a|n|div\.?))*\s*[\)\]]",
        t,
        flags=re.I,
    )
    if m_gender and re.search(r"engineer|developer|entwickler|architect|programmer|specialist", t[: m_gender.start()], re.I):
        t = t[: m_gender.start()]
    else:
        t = re.sub(
            r"\s*[\(\[]\s*(m|w|f|d|x|h|u|a|n|all genders?|gn|mwd|fmd)(\s*[/|,]\s*(m|w|f|d|x|h|u|a|n|div\.?))*\s*[\)\]]",
            "",
            t,
            flags=re.I,
        )
    parts = re.split(r"\s+(?:[-–—|/]|:)\s+", t, maxsplit=1)
    if len(parts) == 2 and re.search(r"engineer|developer|entwickler|architect|programmer|specialist", parts[0], re.I):
        t = parts[0]
    return re.sub(r"\s+", " ", t).strip(" -–|/")


def check_jd_dealbreakers(spec: dict, jd_raw: str) -> list[str]:
    if spec.get("explicit_user_request"):
        return []
    reasons = []
    raw_title = spec.get("title", "")
    jd_body = jd_raw.split("--- JOB DESCRIPTION ---")[-1] if "--- JOB DESCRIPTION ---" in jd_raw else jd_raw

    if HARD_BLOCK_TITLE.search(raw_title):
        reasons.append(f"Blocked title archetype in '{raw_title}' (see REJECTION_POSTMORTEM rule #1)")

    has_paren_senior = bool(re.search(r"\(\s*senior\s*\)", raw_title, re.I))
    title_wo_paren = re.sub(r"\(\s*senior\s*\)", "", raw_title, flags=re.I)
    if re.search(r"\bsenior\b|\bsr\.?\b", title_wo_paren, re.I):
        reasons.append(f"Bare 'Senior' title '{raw_title}' is blocked (46.2% of historical rejections)")
    elif has_paren_senior and not spec.get("allow_parenthetical_senior"):
        reasons.append(
            f"Parenthetical '(Senior)' in '{raw_title}' requires explicit `allow_parenthetical_senior: true` "
            f"after verifying JD states 2-4 / 3+ YOE and openness to mid-level"
        )

    m_de = None
    for _m in GERMAN_KO.finditer(jd_body):
        if "ausreichend" in _m.group(0).lower():
            m_de = _m
            break
        _after = re.split(
            r"\s(?:Nice[- ]to[- ][Hh]ave|Benefits|Das bieten|Wir bieten|Zusätzliche Pluspunkte|Pluspunkte|Darüber hinaus|Außerdem von Vorteil|Folgende Kenntnisse|Folgendes ist|Wünschenswert|Wuenschenswert|Nice to Have)\b|\*\*|\s[Vv]on [Vv]orteil:|(?:[,;]|\s(?:sowie|und|and|as well as))\s*(?:\w+\s+){0,2}(?:Englisch|English)",
            jd_body[_m.end() : _m.end() + 55],
        )[0]
        _ok_after = re.search(
            r"plus|nice to have|optional|bonus|not required|advantage|beneficial|von vorteil|wünschenswert|vorteilhaft|gerne gesehen|kein muss|keinesfalls",
            _m.group(0) + _after,
            re.I,
        )
        _ok_prefix = re.search(
            r"(?:von vorteil|wünschenswert|nice[- ]to[- ]have|ein plus|ein \"?plus\"?|plus|bonus|optional|gerne gesehen)\s*(?::|sind|ist|wären|wäre|w\u00e4ren)\s*$",
            jd_body[max(0, _m.start() - 35) : _m.start()].lower(),
        )
        _sec = jd_body[max(0, _m.start() - 160) : _m.start()]
        _hdr = list(re.finditer(r"(?:Nice[- ]to[- ][Hh]ave|Wünschenswert|Von Vorteil|Plus:|Nice to have)", _sec))
        _req = list(
            re.finditer(
                r"(?:Dein Profil|Das bringst du mit|Was du mitbringst|Anforderungen|Requirements|Must[- ]haves?|Qualifikation|Your profile|What you bring)",
                _sec,
            )
        )
        _in_opt = bool(_hdr) and (not _req or _hdr[-1].start() > _req[-1].start())
        if not (_ok_after or _ok_prefix or _in_opt):
            m_de = _m
            break
    if m_de and not spec.get("override_german_false_positive"):
        ctx_start = max(0, m_de.start() - 25)
        ctx_end = min(len(jd_body), m_de.end() + 55)
        ctx_after = re.split(
            r"\s(?:Nice[- ]to[- ][Hh]ave|Benefits|Das bieten|Wir bieten|Was wir bieten|Unser Angebot|What we offer|Zusätzliche Pluspunkte|Pluspunkte|Darüber hinaus|Außerdem von Vorteil)\b|\*\*|\s[Vv]on [Vv]orteil:|(?:[,;]|\s(?:sowie|und|and|as well as))\s*(?:\w+\s+){0,2}(?:Englisch|English)",
            jd_body[m_de.end() : ctx_end],
        )[0]
        ctx = jd_body[ctx_start : m_de.end()] + ctx_after
        reasons.append(f"German language dealbreaker detected in JD: '{ctx.strip()}'")

    m_yoe = HARD_YOE_KO.search(jd_body) or re.search(
        r"\b(?:mindestens\s+|min\.\s*|at least\s+)?(?:fünf|sechs|sieben|acht|neun|zehn|five|six|seven|eight|nine|ten)\+?\s+(?:jahre|years)",
        jd_body,
        re.I,
    )
    if m_yoe and not spec.get("override_yoe_false_positive"):
        reasons.append(f"Hard 5+ YOE gate detected in JD: '{m_yoe.group(0)}'")

    if CLEARANCE_KO.search(jd_body):
        reasons.append("Defense / security clearance requirement detected in JD")
    if HELPDESK_KO.search(jd_body) and not spec.get("override_helpdesk_false_positive"):
        reasons.append("Internal IT Helpdesk / Servicedesk / Power Platform role detected in JD")

    return reasons


def detect_primary_stack(spec: dict, jd_raw: str) -> str:
    if spec.get("primary_stack") in ("react_nextjs", "vue_nuxt", "node_backend", "fullstack_both", "ai_llm", "webgl_3d"):
        return spec["primary_stack"]
    role = spec.get("role", "").lower()
    title_low = spec.get("title", "").lower()
    jd = jd_raw.lower()
    if role == "3d" or re.search(r"three(?:\.js|js)|react[- ]three[- ]fiber|webgl", jd):
        return "webgl_3d"
    if role == "ai" or re.search(r"\bai engineer\b|applied ai|\bllm\b|\brag\b|langgraph|langchain", title_low):
        return "ai_llm"
    has_vue = bool(re.search(r"\bvue(?:\.js|js)?\b|\bnuxt(?:\.js|js)?\b|\bpinia\b", jd))
    has_react_next = bool(re.search(r"\breact(?:\.js|js)?\b(?!\s*native)|\bnext(?:\.js|js)\b", jd))
    is_fs_or_fe_title = bool(re.search(r"full[- ]?stack|front[- ]?end|\bweb\b|\bui\b", title_low)) or role in ("fullstack", "frontend")
    if role == "backend" or (not is_fs_or_fe_title and not has_vue and not has_react_next and re.search(r"node(?:\.js|js)?|nest(?:\.js|js)|express", jd)):
        return "node_backend"
    if has_vue and not has_react_next:
        return "vue_nuxt"
    if has_react_next and not has_vue:
        return "react_nextjs"
    if has_react_next and has_vue:
        if re.search(r"\bnext(?:\.js|js)\b", jd) and not re.search(r"\bnuxt(?:\.js|js)?\b", jd):
            return "react_nextjs"
        return "fullstack_both"
    return "react_nextjs" if role == "frontend" else "fullstack_both"


STACK_CONFIG = {
    "react_nextjs": {
        "short": "TypeScript, React, Next.js, and Node.js",
        "summary": (
            "{t} with 4+ years of experience building production web applications, customer-facing interfaces, and REST APIs "
            "end to end in TypeScript, JavaScript, React, Next.js, Node.js, and NestJS. Currently owns metering, subscription billing, "
            "and multi-tenant SaaS features from product discovery and API design to production release on SQL, MongoDB, and Redis. "
            "Experienced with event-driven systems, Docker, Kubernetes, Playwright E2E testing, and daily agentic AI workflows (Claude Code)."
        ),
        "order": ["Web and Frameworks", "Data and Messaging", "Testing and Tools", "Cloud and DevOps", "AI Engineering", "Spoken"],
        "skills": {
            "Web and Frameworks": "React, Next.js, Node.js, NestJS, Express.js, HTML5, CSS3, Tailwind CSS, Vite, REST APIs, Vue.js 3",
            "Testing and Tools": "Playwright, Jest, Vitest, React Testing Library, Supertest, Agile, Scrum, Postman, Jira",
        },
        "bullets": [
            (S1, "Own customer-facing SaaS, metering, and subscription billing features from discovery to production with TypeScript, Node.js, Express.js, REST APIs, PostgreSQL, and MongoDB."),
            (M1, "Built responsive web features end to end with React Hooks, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models."),
            (P1, f"Built and shipped {PROJ_DISP} (React 18, TypeScript, Node.js, Express, MongoDB Atlas) and a Next.js portfolio, with JWT moderation and OTP verification."),
        ],
    },
    "vue_nuxt": {
        "short": "TypeScript, Vue.js 3, Pinia, and Node.js",
        "summary": (
            "{t} with 4+ years of experience building responsive web applications and REST APIs end to end in TypeScript, "
            "Vue.js 3 (Composition API, Pinia), Nuxt 3, Tailwind CSS, Vite, and Node.js. Currently builds multi-tenant B2B SaaS "
            f"portals, design-system components, and Express.js, SQL, and MongoDB services at {CUR_EMP}, owning features from discovery "
            "to production. Covered by Vitest and Playwright E2E suites and accelerated daily with Claude Code and AI coding agents."
        ),
        "order": ["Web and Frameworks", "Testing and Tools", "Data and Messaging", "Cloud and DevOps", "AI Engineering", "Spoken"],
        "skills": {
            "Web and Frameworks": "Vue.js 3 (Composition API), Pinia, Nuxt 3, Vite, Tailwind CSS, HTML5, CSS3, Node.js, Express.js, NestJS, React, REST APIs",
            "Testing and Tools": "Vitest, Playwright, Jest, Supertest, ESLint, Agile, Scrum, Postman, Jira",
        },
        "bullets": [
            (S1, "Build multi-tenant web portal features end to end using Vue.js 3 (Composition API, Pinia), Tailwind CSS, TypeScript, Node.js, Express.js, PostgreSQL, and MongoDB."),
        ],
    },
    "node_backend": {
        "short": "TypeScript, Node.js, NestJS, SQL/MongoDB, and Event-Driven Systems",
        "summary": (
            "{t} with 4+ years of experience building production REST APIs, background workers, and event-driven microservices "
            "in TypeScript, Node.js, Express.js, and NestJS backed by PostgreSQL, MSSQL, MongoDB, and Redis. Currently owns metering, "
            f"billing, and multi-tenant services at {CUR_EMP}, cutting a usage-analytics API from 24 s to 3.8 s and eliminating "
            "distributed credit-deduction race conditions across Kubernetes replicas. Ships via Docker, Kubernetes, Helm, CI/CD, and Claude Code."
        ),
        "order": ["Web and Frameworks", "Data and Messaging", "Cloud and DevOps", "Testing and Tools", "AI Engineering", "Spoken"],
        "skills": {
            "Web and Frameworks": "Node.js, NestJS, Express.js, REST APIs, OpenAPI (Swagger), Zod, WebSockets, React, Vue.js 3",
            "Data and Messaging": "PostgreSQL, MSSQL, MySQL, MongoDB (aggregations, transactions), Redis, BullMQ, Redis Streams, GCP Pub/Sub",
        },
        "bullets": [
            (S1, "Design, build, and operate backend services and REST APIs end to end with TypeScript, Node.js, Express.js, OpenAPI, Zod, PostgreSQL, and MongoDB."),
            (M1, "Engineered NestJS REST APIs, BullMQ asynchronous job queues, and MongoDB data models backing a React and TypeScript live-ticketing platform."),
        ],
    },
    "fullstack_both": {
        "short": "TypeScript, Node.js, React, and Vue.js 3",
        "summary": (
            "{t} with 4+ years of experience shipping production web applications and microservices end to end in TypeScript, "
            "Node.js, Express.js, NestJS, Vue.js 3, and React. Currently owns metering, subscription billing, and multi-tenant B2B SaaS features "
            "from product discovery and API design to production release on SQL, MongoDB, and Redis. Experienced with event-driven "
            "architectures, Docker, Kubernetes, Playwright and Vitest testing, and daily AI-assisted engineering with Claude Code."
        ),
        "order": ["Web and Frameworks", "Data and Messaging", "Cloud and DevOps", "Testing and Tools", "AI Engineering", "Spoken"],
        "skills": {
            "Web and Frameworks": "Vue.js 3, Pinia, React, Next.js, Node.js, NestJS, Express.js, Tailwind CSS, Vite, REST APIs",
        },
        "bullets": [
            (S1, "Own B2B SaaS features from product discovery to production release with TypeScript, Vue.js 3, Node.js, Express.js, PostgreSQL, and MongoDB."),
            (M1, "Built live-ticketing features end to end with React Hooks, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models."),
        ],
    },
    "ai_llm": {
        "short": "TypeScript, Node.js, React, LangGraph/LangChain, and RAG",
        "summary": (
            "{t} with 4+ years of full-stack software engineering experience in TypeScript, Node.js, React, and Vue.js 3 paired "
            "with hands-on production LLM engineering across RAG pipelines, LangChain, LangGraph, LlamaIndex, MCP servers, and vector "
            f"search. At {CUR_EMP}, built the {AI_BOT_NAME} support assistant grounded in engineering runbooks via RAG and MongoDB "
            "vector search alongside multi-tenant SaaS and event-driven pipelines."
        ),
        "order": ["AI Engineering", "Web and Frameworks", "Data and Messaging", "Cloud and DevOps", "Testing and Tools", "Spoken"],
        "skills": {
            "AI Engineering": "RAG pipelines, LangChain, LangGraph, LlamaIndex, MCP (Model Context Protocol), AI agents, LLM evaluation, Gemini, Ollama, Claude Code",
            "Web and Frameworks": "React, Next.js, Vue.js 3, Node.js, NestJS, Express.js, WebSockets, REST APIs, Tailwind CSS",
        },
        "bullets": [
            (S1, f"Built the {AI_BOT_NAME} AI assistant using LangGraph, LangChain, MCP, and a RAG pipeline over engineering runbooks and MongoDB vector search, alongside Vue.js 3, TypeScript, Node.js, Express.js, and PostgreSQL SaaS features."),
            (M1, "Built live-ticketing features end to end with React Hooks, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models."),
        ],
    },
    "webgl_3d": {
        "short": "TypeScript, React 19, Three.js, react-three-fiber, and WebGL",
        "summary": (
            "{t} with 4+ years of experience building interactive web applications in TypeScript, React, and Node.js, highlighted "
            "by a Master's thesis multi-client 3D scene viewer engineered with React 19, Three.js, react-three-fiber, @react-three/drei, "
            f"and WebGL. Currently delivers full-stack SaaS features with TypeScript, Vue.js 3, Node.js, SQL, and MongoDB at {CUR_EMP}, "
            "combining 3D scene performance and intuitive spatial UI with reliable production engineering."
        ),
        "order": ["Web and Frameworks", "Testing and Tools", "Data and Messaging", "Cloud and DevOps", "AI Engineering", "Spoken"],
        "skills": {
            "Web and Frameworks": "React 19, Three.js, react-three-fiber, @react-three/drei, WebGL, Next.js, Vue.js 3, Node.js, NestJS, Express.js, Tailwind CSS, REST APIs",
        },
        "bullets": [
            (TH, "an interactive 3D web visualization client (React 19, TypeScript, Three.js, react-three-fiber, @react-three/drei, WebGL) with real-time WebSocket camera synchronization, lighting controls, and level-of-detail GLTF scene streaming across four urban models."),
            (M1, "Built interactive web features end to end with React Hooks, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models."),
        ],
    },
}

FAMILY_ROW = {
    "HTML/CSS": "Web and Frameworks",
    "React": "Web and Frameworks",
    "Next.js": "Web and Frameworks",
    "Vue": "Web and Frameworks",
    "Angular": "Web and Frameworks",
    "Frontend tooling": "Web and Frameworks",
    "Node.js": "Web and Frameworks",
    "APIs": "Web and Frameworks",
    "3D / WebGL": "Web and Frameworks",
    "JavaScript": "Languages",
    "TypeScript": "Languages",
    "Python (tooling level)": "Languages",
    "SQL": "Data and Messaging",
    "MongoDB": "Data and Messaging",
    "Redis & messaging": "Data and Messaging",
    "Cloud & DevOps": "Cloud and DevOps",
    "Git": "Cloud and DevOps",
    "Validation & security": "Cloud and DevOps",
    "Testing": "Testing and Tools",
    "Engineering practices": "Testing and Tools",
    "AI / LLM": "AI Engineering",
}

EXACT_SAFE_DISPLAY = {
    "a11y": "Accessibility (a11y)",
    "wcag": "WCAG",
    "e2e": "E2E",
    "tdd": "TDD",
    "oop": "OOP",
    "spa": "SPA",
    "ssr": "SSR",
    "ssg": "SSG",
    "rbac": "RBAC",
    "jwt": "JWT",
    "json": "JSON",
    "sql": "SQL",
    "nosql": "NoSQL",
    "ci/cd": "CI/CD",
    "gcp": "GCP",
    "gke": "GKE",
    "k8s": "K8s",
    "llm": "LLM",
    "llms": "LLMs",
    "rag": "RAG",
    "mcp": "MCP",
    "genai": "GenAI",
    "r3f": "R3F",
    "webgl": "WebGL",
    "html": "HTML",
    "html5": "HTML5",
    "css": "CSS",
    "css3": "CSS3",
    "scss": "SCSS",
    "js": "JS",
    "ts": "TS",
    "es6": "ES6",
    "es6+": "ES6+",
    "shadcn/ui": "shadcn/ui",
    "shadcn": "shadcn/ui (shadcn)",
    "echarts": "Apache ECharts",
}

LOWERCASE_PREFIX_TECH = {"@react-three/drei", "react-three-fiber", "drei", "npm", "pnpm", "yarn", "nginx", "a11y", "shadcn/ui", "shadcn"}


def set_row(tex, label, line):
    tex, n = re.subn(
        r"(\\textbf\{" + re.escape(label) + r":\} )[^\n]*?(\\\\)?\n",
        lambda m: m.group(1) + line + (m.group(2) or "") + "\n",
        tex,
        count=1,
    )
    assert n == 1, f"Missing skill row label: {label}"
    return tex


def get_row(tex, label):
    return re.search(r"\\textbf\{" + re.escape(label) + r":\} ([^\n]*?)(\\\\)?\n", tex).group(1)


def reorder(tex, order):
    head, rest = tex.split("\\section*{Skills}\n", 1)
    block, tail = rest.split("\n\n", 1)
    rows = {}
    for ln in block.split("\n"):
        ln = ln[:-2] if ln.endswith("\\\\") else ln
        rows[re.match(r"\\textbf\{([^:}]+):\}", ln).group(1)] = ln
    return head + "\\section*{Skills}\n" + "\\\\\n".join(rows[k] for k in ["Languages"] + order) + "\n\n" + tail


def compile_(folder, name, out):
    r = subprocess.run([TECT, str(folder / name), "-o", str(folder)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    pdf, tgt = folder / name.replace(".tex", ".pdf"), folder / out
    if tgt.exists():
        tgt.unlink()
    shutil.move(str(pdf), str(tgt))
    return len(pypdf.PdfReader(str(tgt)).pages)


def format_exact_phrase(jd_clean: str, orig_phrase: str) -> str:
    low = orig_phrase.lower()
    if low in EXACT_SAFE_DISPLAY:
        return EXACT_SAFE_DISPLAY[low]
    if low in LOWERCASE_PREFIX_TECH:
        return low
    matches = [m.group(0) for m in re.finditer(akc.LEFT_BOUND + re.escape(low).replace(r"\ ", r"\s+") + akc.RIGHT_BOUND, jd_clean, re.I)]
    for cand in matches:
        if any(c.isupper() for c in cand):
            return re.sub(r"\s+", " ", cand.strip())
    p = re.sub(r"\s+", " ", orig_phrase.strip())
    return p if any(c.isupper() for c in p) else (p[:1].upper() + p[1:])


def _inject_prose_modifier(tex: str, mod_word: str) -> str:
    for target, repl in (
        ("production web applications", f"{mod_word} web applications"),
        ("responsive web applications", f"{mod_word} responsive web applications"),
        ("B2B SaaS features", f"{mod_word} B2B SaaS features"),
        ("multi-tenant SaaS features", f"{mod_word} multi-tenant SaaS features"),
        ("live-ticketing features", f"{mod_word} live-ticketing features"),
        ("web features", f"{mod_word} web features"),
    ):
        if target in tex:
            return tex.replace(target, repl, 1)
    return tex


def harmonize_prose_compounds(tex: str, jd_clean: str) -> str:
    jd_low = jd_clean.lower()

    if re.search(akc.LEFT_BOUND + r"end-to-end" + akc.RIGHT_BOUND, jd_low):
        if not akc.cv_has_exact_phrase(tex.lower(), tex.lower(), "end-to-end") and "end to end" in tex:
            tex = tex.replace("end to end", "end-to-end", 1)

    wants_hyphen_fs = bool(re.search(akc.LEFT_BOUND + r"full-stack" + akc.RIGHT_BOUND, jd_low))
    wants_oneword_fs = bool(re.search(akc.LEFT_BOUND + r"fullstack" + akc.RIGHT_BOUND, jd_low))
    wants_spaced_fs = bool(re.search(akc.LEFT_BOUND + r"full\s+stack" + akc.RIGHT_BOUND, jd_low))

    non_bold_tex = re.sub(r"\\textbf\{[^}]*\}", " ", tex).lower()
    if wants_hyphen_fs and not akc.cv_has_exact_phrase(non_bold_tex, non_bold_tex, "full-stack"):
        tex = _inject_prose_modifier(tex, "full-stack")
    non_bold_tex = re.sub(r"\\textbf\{[^}]*\}", " ", tex).lower()
    if wants_oneword_fs and not akc.cv_has_exact_phrase(non_bold_tex, non_bold_tex, "fullstack"):
        tex = _inject_prose_modifier(tex, "fullstack")
    non_bold_tex = re.sub(r"\\textbf\{[^}]*\}", " ", tex).lower()
    if wants_spaced_fs and not akc.cv_has_exact_phrase(non_bold_tex, non_bold_tex, "full stack"):
        tex = _inject_prose_modifier(tex, "full stack")

    if re.search(akc.LEFT_BOUND + r"frontend" + akc.RIGHT_BOUND, jd_low) and not akc.cv_has_exact_phrase(tex.lower(), tex.lower(), "frontend"):
        if "reusable React and backend components" in tex:
            tex = tex.replace("reusable React and backend components", "reusable React frontend and backend components", 1)
    if re.search(akc.LEFT_BOUND + r"front-end" + akc.RIGHT_BOUND, jd_low) and not akc.cv_has_exact_phrase(tex.lower(), tex.lower(), "front-end"):
        tex = tex.replace("customer-facing interfaces", "customer-facing front-end interfaces", 1)
    if re.search(akc.LEFT_BOUND + r"back-end" + akc.RIGHT_BOUND, jd_low) and not akc.cv_has_exact_phrase(tex.lower(), tex.lower(), "back-end"):
        if re.search(akc.LEFT_BOUND + r"backend" + akc.RIGHT_BOUND, jd_low):
            tex = tex.replace("reusable React and backend components", "reusable React, back-end, and backend components", 1)
            tex = tex.replace("reusable React frontend and backend components", "reusable React frontend, back-end, and backend components", 1)
        else:
            tex = tex.replace("and backend components", "and back-end components", 1)

    return tex


def _split_skill_items(cur_row: str) -> list[str]:
    return [x.strip() for x in re.split(r",\s*(?![^()]*\))", cur_row) if x.strip()]


def _replace_skill_item(cur_row: str, target_names: tuple[str, ...], new_item: str) -> tuple[str, bool]:
    items = _split_skill_items(cur_row)
    for idx, it in enumerate(items):
        if it.lower() in {t.lower() for t in target_names}:
            items[idx] = new_item
            return ", ".join(items), True
    return cur_row, False


def _add_paren_alias(cur_row: str, anchor_prefixes: tuple[str, ...], alias_disp: str) -> tuple[str, bool]:
    items = _split_skill_items(cur_row)
    for idx, it in enumerate(items):
        it_low = it.lower()
        if any(it_low == p.lower() or it_low.startswith(p.lower() + " (") for p in anchor_prefixes):
            if akc.cv_has_exact_phrase(it_low, it_low, alias_disp.lower()):
                return cur_row, True
            if "(" in it and it.endswith(")"):
                items[idx] = it[:-1] + f", {alias_disp})"
            else:
                items[idx] = f"{it} ({alias_disp})"
            return ", ".join(items), True
    return cur_row, False


def smart_mirror_missing_token(tex: str, fam: str, orig_phrase: str, jd_clean: str) -> tuple[str, str]:
    low = orig_phrase.lower()
    disp = tex_esc(format_exact_phrase(jd_clean, orig_phrase))
    jd_low = jd_clean.lower()

    if low == "js":
        cur = get_row(tex, "Languages")
        upd, ok = _add_paren_alias(cur, ("JavaScript",), "JS")
        if ok:
            return set_row(tex, "Languages", upd), "JavaScript (JS) -> Languages"
    if low == "ts":
        cur = get_row(tex, "Languages")
        upd, ok = _add_paren_alias(cur, ("TypeScript",), "TS")
        if ok:
            return set_row(tex, "Languages", upd), "TypeScript (TS) -> Languages"

    if low in ("react.js", "reactjs"):
        cur = get_row(tex, "Web and Frameworks")
        target_disp = "React.js" if low == "react.js" else "ReactJS"
        upd, ok = _replace_skill_item(cur, ("React", "React 19"), target_disp if "React 19" not in cur else f"React 19 ({target_disp})")
        if not ok:
            upd, ok = _add_paren_alias(cur, ("React.js", "ReactJS", "React"), target_disp)
        if ok:
            return set_row(tex, "Web and Frameworks", upd), f"{target_disp} -> Web and Frameworks"

    if low in ("nextjs", "next.js"):
        cur = get_row(tex, "Web and Frameworks")
        target_disp = "NextJS" if low == "nextjs" else "Next.js"
        other = "next.js" if low == "nextjs" else "nextjs"
        if not re.search(akc.LEFT_BOUND + re.escape(other) + akc.RIGHT_BOUND, jd_low):
            upd, ok = _replace_skill_item(cur, ("Next.js", "NextJS"), target_disp)
        else:
            upd, ok = _add_paren_alias(cur, ("Next.js", "NextJS"), target_disp)
        if ok:
            return set_row(tex, "Web and Frameworks", upd), f"{target_disp} -> Web and Frameworks"

    if low == "nodejs":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _replace_skill_item(cur, ("Node.js",), "NodeJS")
        if not ok:
            upd, ok = _add_paren_alias(cur, ("Node.js", "NodeJS"), "NodeJS")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "NodeJS -> Web and Frameworks"
    if low == "node":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _add_paren_alias(cur, ("Node.js", "NodeJS"), "Node")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "Node -> Web and Frameworks"

    if low == "nest.js":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _replace_skill_item(cur, ("NestJS",), "Nest.js")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "Nest.js -> Web and Frameworks"
    if low == "expressjs":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _replace_skill_item(cur, ("Express.js",), "ExpressJS")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "ExpressJS -> Web and Frameworks"

    if low in ("vue", "vue 3", "vue3", "vuejs"):
        cur = get_row(tex, "Web and Frameworks")
        v_disp = {"vue": "Vue", "vue 3": "Vue 3", "vue3": "Vue3", "vuejs": "VueJS"}[low]
        upd, ok = _add_paren_alias(cur, ("Vue.js 3", "Vue.js 3 (Composition API)", "Vue.js"), v_disp)
        if ok:
            return set_row(tex, "Web and Frameworks", upd), f"{v_disp} -> Web and Frameworks"
    if low in ("nuxt", "nuxt.js", "nuxtjs", "nuxt.js 3"):
        cur = get_row(tex, "Web and Frameworks")
        n_disp = {"nuxt": "Nuxt", "nuxt.js": "Nuxt.js", "nuxtjs": "NuxtJS", "nuxt.js 3": "Nuxt.js 3"}[low]
        upd, ok = _add_paren_alias(cur, ("Nuxt 3", "Nuxt.js"), n_disp)
        if ok:
            return set_row(tex, "Web and Frameworks", upd), f"{n_disp} -> Web and Frameworks"

    if low == "html":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _add_paren_alias(cur, ("HTML5",), "HTML")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "HTML5 (HTML) -> Web and Frameworks"
    if low == "css":
        cur = get_row(tex, "Web and Frameworks")
        upd, ok = _add_paren_alias(cur, ("CSS3",), "CSS")
        if ok:
            return set_row(tex, "Web and Frameworks", upd), "CSS3 (CSS) -> Web and Frameworks"
    if low in ("restful", "restful api", "restful apis"):
        cur = get_row(tex, "Web and Frameworks")
        r_disp = "RESTful API" if low == "restful api" else "RESTful APIs"
        upd, ok = _replace_skill_item(cur, ("REST APIs",), r_disp)
        if ok:
            return set_row(tex, "Web and Frameworks", upd), f"{r_disp} -> Web and Frameworks"

    if low == "postgres":
        cur = get_row(tex, "Data and Messaging")
        upd, ok = _add_paren_alias(cur, ("PostgreSQL",), "Postgres")
        if ok:
            return set_row(tex, "Data and Messaging", upd), "PostgreSQL (Postgres) -> Data and Messaging"
    if low in ("nosql", "mongo"):
        cur = get_row(tex, "Data and Messaging")
        m_disp = "NoSQL" if low == "nosql" else "Mongo"
        upd, ok = _add_paren_alias(cur, ("MongoDB", "MongoDB (aggregations, transactions)"), m_disp)
        if ok:
            return set_row(tex, "Data and Messaging", upd), f"MongoDB ({m_disp}) -> Data and Messaging"
    if low == "k8s":
        cur = get_row(tex, "Cloud and DevOps")
        upd, ok = _add_paren_alias(cur, ("Kubernetes",), "K8s")
        if ok:
            return set_row(tex, "Cloud and DevOps", upd), "Kubernetes (K8s) -> Cloud and DevOps"
    if low == "google cloud":
        cur = get_row(tex, "Cloud and DevOps")
        upd, ok = _add_paren_alias(cur, ("GCP",), "Google Cloud")
        if ok:
            return set_row(tex, "Cloud and DevOps", upd), "GCP (Google Cloud) -> Cloud and DevOps"

    if low in ("full-stack", "fullstack", "full stack"):
        new_tex = _inject_prose_modifier(tex, low)
        if new_tex != tex:
            return new_tex, f"{low} -> prose"
        return tex, ""
    if low in ("frontend", "front-end", "backend", "back-end"):
        if "reusable React and backend components" in tex:
            return (
                tex.replace("reusable React and backend components", f"reusable React {low} and backend components", 1),
                f"{low} -> prose",
            )
        return tex, ""

    row = FAMILY_ROW.get(fam, "Testing and Tools")
    cur = get_row(tex, row)
    if not akc.cv_has_exact_phrase(cur.lower(), cur.lower(), low):
        tex = set_row(tex, row, cur + ", " + disp)
        return tex, f"{disp} -> {row}"
    return tex, ""


def dedup_skill_rows(tex: str) -> str:
    seen_low: set[str] = set()
    row_priority = [
        "Languages",
        "Web and Frameworks",
        "Data and Messaging",
        "Cloud and DevOps",
        "Testing and Tools",
        "AI Engineering",
    ]
    for rname in row_priority:
        items = _split_skill_items(get_row(tex, rname))
        kept = []
        for it in items:
            key = it.lower().strip()
            if key not in seen_low:
                seen_low.add(key)
                kept.append(it)
        if kept and len(kept) != len(items):
            tex = set_row(tex, rname, ", ".join(kept))
    return tex


CL_BANNED_AI_RE = re.compile(
    r"\b(?:tailored|tailor|customi[sz]ed|bespoke|seamlessly|seamless|uncompromising|rock-solid|"
    r"relentlessly|delighted|thrilled|passionate|excited|leverage|leveraging|synergy|cutting-edge|"
    r"uniquely positioned|testament to|honed my skills)\b"
    r"|at the intersection of|the exact environment i thrive in|\bthrive in\b|aligns directly|i am writing to express",
    re.I,
)


def humanize_cl_text(s: str) -> str:
    """Strip AI tells (bold headings, dashes ' - '/'--'/'—'/'–', semicolons, AI clichés) so Cover Letters read 100% human."""
    s = re.sub(r"^\s*\\textbf\{[^}]*?:\}\s*", "", s)
    s = re.sub(r"\s*(?:---|--|—|–)\s*", ", ", s)
    s = re.sub(r"\s+-\s+", ", ", s)
    s = re.sub(r";\s+([a-z])", lambda m: ". " + m.group(1).upper(), s)
    s = re.sub(
        r"\b(?:seamlessly|seamless|uncompromising|rock-solid|relentlessly|delighted|thrilled|passionate|excited|cutting-edge)\b\s*",
        "",
        s,
        flags=re.I,
    )
    s = re.sub(r"\bleveraging\b", "using", s, flags=re.I)
    s = re.sub(r"\bleverage\b", "use", s, flags=re.I)
    s = re.sub(r"sits right at the intersection of", "combines", s, flags=re.I)
    s = re.sub(r"at the intersection of", "combining", s, flags=re.I)
    s = re.sub(r"is the exact environment I thrive in", "is how I like to work", s, flags=re.I)
    s = re.sub(r",\s*,+", ", ", s)
    return re.sub(r"\s+", " ", s).strip()


def build_default_cl_bullets(pstack: str, anti_ai: bool = False) -> list[str]:
    b_backend = (
        f"In my current role at {CUR_EMP} in {CUR_CITY}, I work on multi-tenant SaaS, metering, and subscription billing services. "
        r"Recently, I cut a slow workspace usage-analytics API from $\sim$24\,s down to $\sim$3.8\,s by caching closed billing windows in Redis "
        r"and consolidating live reads into a single indexed MongoDB aggregation, prevented duplicate credit deductions across "
        r"Kubernetes replicas with an atomic compare-and-set, hardened tenant API isolation (JWT/OAuth 2.0, RBAC), and built "
        r"event-driven workers using GCP Pub/Sub, Redis Streams, Docker, and Helm."
    )
    if anti_ai:
        b_ai = (
            r"I write clean, maintainable code from first principles and back what I ship with peer code reviews and "
            r"automated tests across Playwright E2E, Vitest, and Jest."
        )
    else:
        b_ai = (
            r"I also use Claude Code in my daily workflow to move faster while keeping full ownership of the architecture, "
            r"edge cases, and automated Playwright, Vitest, and Jest tests."
        )
    if pstack == "react_nextjs":
        b1 = (
            f"At {PREV1_EMP}, I built customer-facing web features end to end with React Hooks, TypeScript, NestJS REST APIs, "
            f"and BullMQ background jobs, and at {PREV2_EMP} I spent two years building enterprise billing interfaces in React and SQL. "
            f"Outside of work, I built and maintain \\href{{{PROJ_URL}}}{{{PROJ_DISP}}} (React 18, TypeScript, Node.js, "
            r"Express, MongoDB) across 40+ zero-downtime releases."
        )
        return [b1, b_backend, b_ai]
    if pstack == "vue_nuxt":
        b1 = (
            f"At {CUR_EMP}, I build and release multi-tenant web portal features and reusable UI components using Vue.js 3 "
            r"(Composition API, Pinia), Vite, Tailwind CSS, TypeScript, and Node.js/Express REST APIs, covered by Vitest and "
            r"Playwright E2E tests."
        )
        return [b1, b_backend, b_ai]
    if pstack == "webgl_3d":
        b1 = (
            f"For my Master's thesis at {EDU_UNI}, I built a collaborative browser-based 3D urban scene viewer in React 19, "
            r"TypeScript, Three.js, react-three-fiber, and @react-three/drei with real-time WebSocket camera synchronization "
            r"and level-of-detail GLTF scene streaming across four urban models."
        )
        return [b1, b_backend, b_ai]
    if pstack == "ai_llm":
        b1 = (
            f"At {CUR_EMP}, I built {AI_BOT_NAME}, our internal support assistant, using a RAG pipeline over engineering runbooks, "
            r"MongoDB vector search, LangChain, LangGraph, and MCP servers integrated into our TypeScript, Node.js, and Vue.js 3 platform."
        )
        return [b1, b_backend, b_ai]
    b1 = (
        f"Across {CUR_EMP}, {PREV1_EMP}, and {PREV2_EMP}, I've owned web features and backend APIs from initial design through "
        r"production in TypeScript, Node.js, Express, NestJS, Vue.js 3, and React, and I also built and maintain "
        f"\\href{{{PROJ_URL}}}{{{PROJ_DISP}}} across 40+ releases."
    )
    return [b1, b_backend, b_ai]


def build_cover_letter(spec: dict, folder: Path, title: str, pstack: str, anti_ai: bool = False) -> None:
    scfg = STACK_CONFIG[pstack]
    comp_esc = humanize_cl_text(tex_esc(spec["company"]))
    loc_esc = humanize_cl_text(tex_esc(spec["location"]))
    title_esc = humanize_cl_text(tex_esc(title))
    raw_short = (spec.get("stack_short") or "").strip()
    if not raw_short or raw_short.count(",") > 3:
        raw_short = scfg["short"]
    short_esc = tex_esc(raw_short)

    hook = humanize_cl_text(spec.get("cl_hook") or "")
    if spec.get("cl_opening"):
        opening = humanize_cl_text(spec["cl_opening"])
    else:
        opening = (
            f"I'm applying for the \\textbf{{{title_esc}}} role at {comp_esc}. Over the past four years across {CUR_EMP}, "
            f"{PREV1_EMP}, and {PREV2_EMP}, I've built and run production web applications, REST APIs, and background services "
            f"in {short_esc}. {hook}".strip()
        )

    raw_bullets = spec.get("cl_bullets")
    if isinstance(raw_bullets, list) and len(raw_bullets) == 3:
        formatted_bullets = []
        for b in raw_bullets:
            if isinstance(b, dict):
                formatted_bullets.append(humanize_cl_text(b["body"]))
            else:
                formatted_bullets.append(humanize_cl_text(str(b)))
    else:
        formatted_bullets = build_default_cl_bullets(pstack, anti_ai=anti_ai)

    city = tex_esc(spec["location"].split(",")[0].strip())
    sal_clause = ""
    if spec.get("include_salary_in_cl") and spec.get("salary"):
        sal_clause = f" My salary expectation is around EUR {tex_esc(str(spec['salary']))} gross per year."

    closing = humanize_cl_text(spec.get("cl_closing") or "") or (
        f"I'm finishing my {EDU_DEG} at {EDU_UNI} in {EDU_GRAD} and can start full-time "
        f"from {START_PROSE} with a valid German work permit. I speak fluent English and A2 German (actively improving), "
        f"and I'm happy to work on-site or hybrid in {city}.{sal_clause}"
    )

    cl = (H / "MASTER_COVER_LETTER_TEMPLATE.tex").read_text(encoding="utf-8")
    cl = (
        cl.replace("__COMPANY_ESC__", comp_esc)
        .replace("__LOC_ESC__", loc_esc)
        .replace("__TITLE_ESC__", title_esc)
        .replace("__STACK_SHORT_ESC__", short_esc)
        .replace("__CL_OPENING__", opening)
        .replace("__CL_BULLET_1__", formatted_bullets[0])
        .replace("__CL_BULLET_2__", formatted_bullets[1])
        .replace("__CL_BULLET_3__", formatted_bullets[2])
        .replace("__CL_CLOSING__", closing)
    )
    (folder / "cover_letter.tex").write_text(cl, encoding="utf-8")
    cl_pages = compile_(folder, "cover_letter.tex", CLP)
    assert cl_pages == 1, f"FAIL: Cover letter must be strictly 1 page, got {cl_pages} pages"
    cl_txt = " ".join((p.extract_text() or "") for p in pypdf.PdfReader(str(folder / CLP)).pages)
    assert "__" not in cl_txt, f"FAIL: Unreplaced placeholder left in {CLP}"
    m_ai = CL_BANNED_AI_RE.search(cl_txt)
    assert not m_ai, f"FAIL: AI-sounding phrase '{m_ai.group(0)}' found in {CLP}"
    cl_body = cl_txt.split("Subject:", 1)[-1] if "Subject:" in cl_txt else cl_txt
    assert not re.search(r"—|–|\s-\s|•", cl_body), (
        f"FAIL: Cover letter body must be 100% humanized prose with ZERO dashes ('—', '–', ' - ') and ZERO bullets ('•') in {CLP}"
    )


def main(spec_path: str) -> bool:
    raw = Path(spec_path).read_text(encoding="utf-8-sig")
    spec = json.loads(raw)
    folder = Path(spec["folder"])
    jd_txt = (folder / "Job_Description.txt").read_text(encoding="utf-8", errors="ignore")
    jd_clean = akc.prepare_jd_text(jd_txt)

    # 1. Hard Pre-Build Zero-Rejection Gate
    dealbreakers = check_jd_dealbreakers(spec, jd_txt)
    if dealbreakers:
        print("BLOCKED BY ZERO-REJECTION GATE (DO NOT APPLY):")
        for d in dealbreakers:
            print("  -", d)
        sys.exit(2)

    title = clean_title(spec["title"])
    pstack = detect_primary_stack(spec, jd_txt)
    scfg = STACK_CONFIG[pstack]
    anti_ai = bool(ANTI_AI_KO.search(jd_txt))

    tex = (H / "MASTER_RESUME_TEMPLATE.tex").read_text(encoding="utf-8")
    eng_title = re.sub(r"Softwareentwickler(?:in)?", "Software Developer", title, flags=re.I)
    eng_title = re.sub(r"Webentwickler(?:in)?", "Web Developer", eng_title, flags=re.I)
    eng_title = re.sub(r"Entwickler(?:in)?", "Developer", eng_title, flags=re.I)
    summary = spec.get("summary") or scfg["summary"].format(t=tex_esc(eng_title))
    summary = re.sub(
        r"\s*[\(\[]\s*(?:m|w|f|d|x|h|u|a|n|all genders?|gn|mwd|fmd)(?:\s*[/|,]\s*(?:m|w|f|d|x|h|u|a|n|div\.?))*\s*[\)\]]",
        "",
        summary,
        flags=re.I,
    )
    summary = re.sub(r"^([A-Za-z0-9/+\- ]*?)\bSoftwareentwickler(?:in)?\b", r"\1Software Developer", summary)
    summary = re.sub(r"^([A-Za-z0-9/+\- ]*?)\bWebentwickler(?:in)?\b", r"\1Web Developer", summary)
    summary = re.sub(r"^([A-Za-z0-9/+\- ]*?)\bEntwickler(?:in)?\b", r"\1Developer", summary)
    if anti_ai:
        summary = re.sub(r",?\s*and daily (?:agentic AI workflows \(Claude Code\)|AI-assisted engineering with Claude Code)", "", summary, flags=re.I)
        summary = re.sub(r"\s*and accelerated daily with Claude Code and AI coding agents", "", summary, flags=re.I)
        summary = re.sub(r",?\s*(?:and )?uses Claude Code(?: and AI coding agents)? daily", "", summary, flags=re.I)
        summary = re.sub(r",?\s*with Claude Code", "", summary, flags=re.I)
    tex = re.sub(
        r"(\\section\*\{Summary\}\n)(.*?)(\n\n)",
        lambda m: m.group(1) + summary + m.group(3),
        tex,
        count=1,
        flags=re.S,
    )

    skill_overrides = {
        **scfg.get("skills", {}),
        **{k: (", ".join(v) if isinstance(v, list) else str(v)) for k, v in spec.get("extra_skills_replace", {}).items()},
    }
    if anti_ai and "AI Engineering" not in spec.get("extra_skills_replace", {}):
        skill_overrides["AI Engineering"] = "RAG, LLM applications, LangChain, LlamaIndex, LangGraph, MCP, Ollama"
    for label, line in skill_overrides.items():
        tex = set_row(tex, label, line)
    if anti_ai:
        ai_cur = get_row(tex, "AI Engineering")
        ai_cleaned = [x for x in _split_skill_items(ai_cur) if not re.search(r"claude|coding agent|copilot|cursor", x, re.I)]
        if ai_cleaned:
            tex = set_row(tex, "AI Engineering", ", ".join(ai_cleaned))

    for old, new in scfg.get("bullets", []):
        tex = tex.replace(old, new, 1)
    for old, new in spec.get("bullet_rewrites", []):
        tex = tex.replace(old, new, 1)

    if re.search(r"\bangular\b", jd_clean, re.I):
        wf_cur = get_row(tex, "Web and Frameworks")
        if not re.search(r"\bangular\b", wf_cur, re.I):
            tex = set_row(tex, "Web and Frameworks", wf_cur + ", Angular")

    wants_ai_exp = (not anti_ai) and bool(
        re.search(r"\b(?:llm|llms|rag|langchain|langgraph|llamaindex|genai|ai\s+agents?|ai\s+features|künstliche\s+intelligenz)\b", jd_clean + " " + summary, re.I)
        or re.search(r"\bKI(?:-[A-Za-zÄÖÜäöüß]+)?\b", jd_clean)
    )
    if wants_ai_exp and f"\\textbf{{{CUR_EMP_HDR}}}" in tex and f"\\textbf{{{PREV1_EMP_HDR}}}" in tex:
        cur_part = tex.split(f"\\textbf{{{CUR_EMP_HDR}}}", 1)[-1].split(f"\\textbf{{{PREV1_EMP_HDR}}}", 1)[0]
        if not re.search(r"\b(?:rag|llm|llms|langgraph|langchain|mcp)\b", cur_part, re.I):
            tex = re.sub(
                r"(\\textbf\{" + re.escape(CUR_EMP_HDR) + r"\}.*?\\begin\{itemize\}\s*\\item\s+)([^\n]+)",
                lambda m: m.group(1) + m.group(2).rstrip(".") + ", including LLM and RAG workflows.",
                tex,
                count=1,
                flags=re.S,
            )

    tex = harmonize_prose_compounds(tex, jd_clean)
    tex = dedup_skill_rows(tex)

    # 2. Build 100% Humanized Cover Letter
    build_cover_letter(spec, folder, title, pstack, anti_ai=anti_ai)

    # 3. Compile Resume + Mirror Missing Verified JD Keywords (Exact Punctuation & Token Boundaries)
    order = spec.get("skill_order") or scfg["order"]
    added: list[str] = []
    all_jd_phrases_low: set[str] = set()
    pages = 1

    for _ in range(4):
        tex = dedup_skill_rows(tex)
        t2 = reorder(tex, order)
        (folder / "resume.tex").write_text(t2, encoding="utf-8")
        pages = compile_(folder, "resume.tex", RES)
        eval_res = akc.evaluate_jd_against_pdf(jd_txt, str(folder / RES))
        for _, p_cov in eval_res["covered_pairs"]:
            all_jd_phrases_low.add(p_cov.lower())
        for _, p_miss in eval_res["missing_pairs"]:
            all_jd_phrases_low.add(p_miss.lower())
        if not eval_res["missing_pairs"]:
            break
        progressed = False
        for fam, orig_ph in eval_res["missing_pairs"]:
            new_tex, log_entry = smart_mirror_missing_token(tex, fam, orig_ph, jd_clean)
            if log_entry and new_tex != tex:
                tex = new_tex
                added.append(log_entry)
                progressed = True
        if not progressed:
            break

    # 4. Trim cleanly if 2 pages while strictly protecting ALL JD-matched tokens
    def _item_is_jd_protected(item_str: str) -> bool:
        it_l = item_str.lower()
        for jdp in all_jd_phrases_low:
            if akc.cv_has_exact_phrase(it_l, it_l, jdp):
                return True
        return False

    guard = 0
    while pages > 1 and guard < 16:
        guard += 1
        trimmed_any = False
        for row in ["Cloud and DevOps", "Testing and Tools", "Data and Messaging", "AI Engineering", "Web and Frameworks"]:
            items = _split_skill_items(get_row(tex, row))
            for i in range(len(items) - 1, -1, -1):
                if len(items) <= 4:
                    break
                if not _item_is_jd_protected(items[i]):
                    items.pop(i)
                    trimmed_any = True
                    break
            tex = set_row(tex, row, ", ".join(items))
            (folder / "resume.tex").write_text(reorder(tex, order), encoding="utf-8")
            pages = compile_(folder, "resume.tex", RES)
            if pages == 1:
                break
        if not trimmed_any:
            break

    r = subprocess.run([PY, str(H / "validate_resume_pdf.py"), str(folder / RES)], capture_output=True, text=True)
    qa = (r.stdout + r.stderr).strip().splitlines()[-1]
    k = subprocess.run(
        [PY, str(H / "ats_keyword_check.py"), str(folder / "Job_Description.txt"), str(folder / RES)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(f"PRIMARY_STACK: {pstack}")
    print(qa)
    print("ADDED:", "; ".join(added) or "none")
    print("\n".join(ln for ln in k.stdout.splitlines() if not ln.startswith("COVERED")))
    return (
        qa.startswith("PASS")
        and "MISSING (known skill, add JD's exact wording to CV): none" in k.stdout
        and "FORBIDDEN-IN-CV: none" in k.stdout
    )


if __name__ == "__main__":
    ok = main(sys.argv[1])
    print("AUTO_TAILOR:", "OK" if ok else "NEEDS MANUAL FIX")
    sys.exit(0 if ok else 1)
