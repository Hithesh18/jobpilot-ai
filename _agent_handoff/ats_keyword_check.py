r"""
Exact-Punctuation & Token-Boundary ATS Keyword Gate (`_agent_handoff/ats_keyword_check.py`)
Shared by Claude Code & Gemini Antigravity — Cross-Platform Native Python.

Usage:
  python _agent_handoff/ats_keyword_check.py "<job_folder>/Job_Description.txt" "<job_folder>/<Resume>.pdf"

Why Exact Punctuation & Token Boundaries Matter:
  Real ATS screening filters (Workday, Greenhouse, Lever, Personio, Teamtailor, SmartRecruiters / Lucene UAX#29)
  treat `React.js` != `React` != `ReactJS`, `Node.js` != `NodeJS` != `Node`, `Next.js` != `NextJS`,
  `NestJS` != `Nest.js`, `PostgreSQL` != `Postgres`, `MongoDB` != `NoSQL`, `Kubernetes` != `K8s`,
  `TypeScript` != `TS`, `JavaScript` != `JS`, `Full-Stack` != `Full Stack` != `Fullstack`,
  and `end-to-end` != `end to end` != `E2E`.

  Therefore this gate:
    1. NEVER strips dots (`.`), hyphens (`-`), slashes (`/`), or spaces into a lossy `cv_compact` blob.
    2. NEVER conflates abbreviations (`K8s`, `NoSQL`, `Postgres`, `JS`, `TS`, `Node`, `E2E`) with their full names.
    3. Scans ALL occurrences in the JD (no early `break` on first match) so if a JD writes `React` in the intro
       AND `React.js` in Requirements, BOTH literal tokens must exist in the compiled 1-page Resume PDF.
    4. Fails (`exit 1`) if any unverified/forbidden skill (`NEVER`) appears anywhere in the CV.
"""
import re
import sys
from pathlib import Path

import pypdf

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_loader import load_profile  # noqa: E402

# UAX#29 / ATS-safe token boundaries:
# - Left:  not preceded by alphanumeric/`+`/`#`/`@`/`-`, and not preceded by `<alnum>.` (so `.js` in `Node.js` never matches bare `JS`).
# - Right: not followed by alphanumeric/`+`/`#`/`-`, and not followed by `.<alnum>` (so `React.js` never falsely satisfies bare `React`,
#          while sentence-ending `React.` followed by whitespace/EOF DOES satisfy `React`).
LEFT_BOUND = r"(?<![a-z0-9+#@-])(?<![a-z0-9]\.)"
RIGHT_BOUND = r"(?![a-z0-9+#-])(?!\.[a-z0-9])"

# Default verified skill families (keep in sync with CURRENT_COMPANY_TECH_STACK.md and candidate_profile.json).
# Every distinct punctuation / dot / hyphen / abbreviation spelling found in the JD is checked verbatim.
KNOWN = {
    "JavaScript": [
        r"javascript",
        r"ecmascript",
        r"es6\+?",
        r"js",
    ],
    "TypeScript": [
        r"typescript",
        r"ts",
    ],
    "HTML/CSS": [
        r"html5?",
        r"css3?",
        r"scss",
        r"sass",
        r"responsive (?:web )?design",
        r"semantic html",
        r"web accessibility|accessibility",
        r"a11y",
        r"wcag",
        r"web components?",
        r"cross[- ]browser",
    ],
    "React": [
        r"react(?:\.js|js)?(?!\s*native)",
        r"react hooks?",
        r"redux(?: toolkit)?",
        r"context api",
        r"jsx",
        r"tsx",
        r"component[- ]based",
        r"component architecture",
        r"reusable components?",
        r"state management",
        r"single[- ]page applications?",
        r"spa",
        r"react testing library",
        r"react query",
        r"tanstack(?: query)?",
        r"virtual dom",
    ],
    "Next.js": [
        r"next(?:\.js|js)",
        r"server[- ]side rendering",
        r"ssr",
        r"static site generation",
        r"ssg",
        r"app router",
    ],
    "Vue": [
        r"vue(?:\.js|js)?(?:\s*3)?",
        r"composition api",
        r"pinia",
        r"vuex",
        r"nuxt(?:\.js|js)?(?:\s*3)?",
        r"vue router",
    ],
    "Angular": [
        r"angular(?:\.js|js)?",
    ],
    "Frontend tooling": [
        r"vite",
        r"webpack",
        r"tailwind(?:\s*css)?",
        r"shadcn(?:/ui)?",
        r"design systems?",
        r"component librar(?:y|ies)",
        r"echarts",
        r"npm",
        r"pnpm",
        r"yarn",
        r"eslint",
        r"prettier",
    ],
    "Node.js": [
        r"node(?:\.js|js)?",
        r"express(?:\.js|js)",
        r"nest(?:\.js|js)",
        r"async/await",
        r"asynchronous programming",
        r"event loop",
    ],
    "APIs": [
        r"restful(?: apis?)?",
        r"rest apis?",
        r"api design",
        r"openapi",
        r"swagger",
        r"websockets?",
        r"webhooks?",
        r"third[- ]party (?:apis?|services|integrations?)",
        r"api integrations?",
        r"json",
    ],
    "Validation & security": [
        r"zod",
        r"jwt",
        r"oauth\s*2?(?:\.0)?",
        r"rbac",
        r"role[- ]based access(?: control)?",
        r"authentication",
        r"authori[sz]ation",
        r"owasp",
        r"security best practices",
        r"(?:common )?security vulnerabilit(?:y|ies)",
        r"multi[- ]tenan(?:t|cy)",
    ],
    "SQL": [
        r"sql",
        r"postgresql",
        r"postgres",
        r"mysql",
        r"mssql",
        r"sql server",
        r"t-sql",
        r"relational databases?",
        r"data model(?:l)?ing",
        r"database design",
        r"query optimi[sz]ation",
        r"database indexing",
    ],
    "MongoDB": [
        r"mongodb",
        r"mongo",
        r"nosql",
        r"aggregation pipelines?",
        r"vector (?:search|store|databases?)",
    ],
    "Redis & messaging": [
        r"redis",
        r"caching",
        r"bullmq",
        r"message queues?",
        r"job queues?",
        r"background jobs?",
        r"pub/sub",
        r"pubsub",
        r"redis streams",
        r"event[- ]driven(?: architecture)?",
        r"micro-?services?",
        r"distributed systems?",
    ],
    "Cloud & DevOps": [
        r"docker",
        r"containeri[sz]ation",
        r"kubernetes",
        r"k8s",
        r"helm",
        r"gke",
        r"google cloud",
        r"gcp",
        r"ci/cd",
        r"continuous integration",
        r"continuous delivery",
        r"continuous deployment",
        r"gitlab(?: ci)?",
        r"github actions",
        r"gitops",
        r"flux",
        r"devops",
        r"linux",
        r"unix",
        r"nginx",
        r"monitoring",
        r"observability",
        r"opentelemetry",
        r"prometheus",
    ],
    "Git": [
        r"git",
        r"git workflows?",
        r"version control",
        r"source control",
        r"branching(?: strategies)?",
        r"pull requests?",
        r"merge requests?",
        r"code reviews?",
    ],
    "Testing": [
        r"unit tests?",
        r"unit testing",
        r"integration tests?",
        r"integration testing",
        r"end[- ]to[- ]end",
        r"e2e",
        r"tdd",
        r"test[- ]driven(?: development)?",
        r"playwright",
        r"jest",
        r"vitest",
        r"supertest",
        r"test automation",
        r"automated test(?:s|ing)?",
        r"debugging",
    ],
    "Engineering practices": [
        r"full[- ]stack",
        r"fullstack",
        r"front[- ]end",
        r"frontend",
        r"back[- ]end",
        r"backend",
        r"agile",
        r"scrum",
        r"kanban",
        r"clean code",
        r"solid principles?",
        r"design patterns?",
        r"object[- ]oriented(?: programming)?",
        r"oop",
        r"functional programming",
        r"software architecture",
        r"system design",
        r"technical documentation",
        r"pair programming",
        r"jira",
        r"postman",
    ],
    "AI / LLM": [
        r"llms?",
        r"large language models?",
        r"generative ai",
        r"genai",
        r"rag",
        r"retrieval[- ]augmented(?: generation)?",
        r"langchain",
        r"langgraph",
        r"llamaindex",
        r"mcp",
        r"model context protocol",
        r"ai agents?",
        r"agentic",
        r"prompt engineering",
        r"embeddings?",
        r"ollama",
        r"gemini",
        r"claude(?: code)?",
        r"ai coding (?:agents|assistants|tools)",
        r"copilot",
        r"cursor",
    ],
    "3D / WebGL": [
        r"three(?:\.js|js)",
        r"react[- ]three[- ]fiber",
        r"r3f",
        r"webgl",
        r"@react-three/drei",
    ],
    "Python (tooling level)": [
        r"python",
    ],
}

# Unverified skills the candidate does NOT have: NEVER place in CV (Tier 3 in ATS_Analysis.md only).
NEVER = {
    "Go/Golang": r"\bgolang\b|\bgo\b(?=\s*(?:,|/|\)|developer|engineer|lang|programming|services|backend))",
    "C#/.NET": r"c#|(?<![a-z0-9])\.net\b|asp\.net|\bdotnet\b|\bblazor\b",
    "Java/Spring": r"\bjava\b(?!script)|spring boot|\bspring\b|\bjvm\b",
    "Kotlin": r"\bkotlin\b",
    "C/C++": r"c\+\+|\bembedded c\b",
    "Rust": r"\brust\b",
    "PHP": r"\bphp\b|\blaravel\b|\bsymfony\b|\bwordpress\b|\btypo3\b",
    "Ruby/Rails": r"\bruby\b|\brails\b",
    "Scala": r"\bscala\b",
    "Mobile native": r"react native|\bexpo\b|\bswift\b|\bios\b|\bandroid\b|\bflutter\b",
    "GraphQL": r"\bgraphql\b|\bapollo\b",
    "AWS": r"\baws\b|amazon web services|\blambda\b",
    "Azure (production)": r"azure (?:functions|devops|kubernetes|cloud services)",
    "Kafka": r"\bkafka\b",
    "Terraform/Pulumi": r"\bterraform\b|\bpulumi\b|\bsst\b",
    "Django/FastAPI": r"\bdjango\b|\bfastapi\b|\bflask\b",
    "SAP/Salesforce": r"\bsap\b|\bsalesforce\b|\bhubspot\b|\bmendix\b",
}

_PROF = load_profile()
if isinstance(_PROF.get("custom_known_skills"), dict):
    KNOWN.update(_PROF["custom_known_skills"])
if isinstance(_PROF.get("custom_never_skills"), dict):
    NEVER.update(_PROF["custom_never_skills"])


def _norm_dashes_and_ligatures(text: str) -> str:
    return (
        text.replace("\ufb00", "ff")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\ufb03", "ffi")
        .replace("\ufb04", "ffl")
        .replace("\u2010", "-")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
    )


def prepare_jd_text(jd_raw: str) -> str:
    txt = _norm_dashes_and_ligatures(jd_raw)
    title_lines = re.findall(r"(?im)^(?:job\s+title|title|position|role)\s*:\s*(.+)$", txt)
    if re.search(r"(?i)---\s*job description\s*---", txt):
        body = re.split(r"(?i)---\s*job description\s*---", txt, maxsplit=1)[-1]
    elif "\n---\n" in txt:
        body = txt.split("\n---\n", 1)[-1]
    else:
        body = re.sub(
            r"(?im)^(?:apply\s+url|url|company\s+careers\s+url|linkedin\s+job\s+url|direct\s+application\s+url|source|portal)\s*:.*$",
            " ",
            txt,
        )
    combined = "\n".join(title_lines) + "\n" + body
    combined = re.sub(r"https?://\S+|www\.\S+", " ", combined)
    return re.sub(r"\s+", " ", combined).strip()


def prepare_cv_texts(pdf_path: str) -> tuple[str, str]:
    raw = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(pdf_path).pages)
    raw = _norm_dashes_and_ligatures(raw).lower()
    links_cfg = _PROF.get("candidate", {}).get("links", {})
    extra_hosts = [
        re.escape(links_cfg.get("portfolio_display", "")).lower(),
        re.escape(links_cfg.get("flagship_project_display", "")).lower(),
    ]
    host_pat = "|".join(["linkedin\\.com", "github\\.com"] + [h for h in extra_hosts if h])
    raw_no_urls = re.sub(r"(?:https?://)?(?:" + host_pat + r")\S*", " ", raw)
    cv_hyphen = re.sub(r"\s+", " ", re.sub(r"(?<=[a-z0-9])-\s*\n\s*(?=[a-z0-9])", "-", raw_no_urls))
    cv_joined = re.sub(r"\s+", " ", re.sub(r"(?<=[a-z0-9])-\s*\n\s*(?=[a-z0-9])", "", raw_no_urls))
    return cv_hyphen, cv_joined


def cv_has_exact_phrase(cv_hyphen: str, cv_joined: str, phrase_low: str) -> bool:
    escaped = re.escape(phrase_low).replace(r"\ ", r"\s+")
    rx = re.compile(LEFT_BOUND + r"(?:" + escaped + r")" + RIGHT_BOUND, re.I)
    if "-" in phrase_low:
        return bool(rx.search(cv_hyphen))
    return bool(rx.search(cv_hyphen) or rx.search(cv_joined))


def evaluate_jd_against_pdf(jd_raw: str, pdf_path: str) -> dict:
    jd_clean = prepare_jd_text(jd_raw)
    jd_low = jd_clean.lower()
    cv_hyphen, cv_joined = prepare_cv_texts(pdf_path)

    missing_pairs: list[tuple[str, str]] = []
    covered_pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for fam, pats in KNOWN.items():
        for pat in pats:
            rx = re.compile(LEFT_BOUND + r"(?:" + pat + r")" + RIGHT_BOUND, re.I)
            for m in rx.finditer(jd_clean):
                orig_phrase = re.sub(r"\s+", " ", m.group(0).strip())
                low_phrase = orig_phrase.lower()
                if not low_phrase or (fam, low_phrase) in seen:
                    continue
                prefix_ctx = jd_low[max(0, m.start() - 30) : m.start()]
                if re.search(r"\b(?:no|not|without|never|kein|keine|ohne)\s+(?:[a-z0-9_-]+\s+){0,2}$", prefix_ctx):
                    continue
                if low_phrase == "node" and orig_phrase == "node":
                    ctx = jd_low[max(0, m.start() - 25) : min(len(jd_low), m.end() + 25)]
                    if not re.search(r"js|ts|typescript|javascript|react|vue|angular|nest|express|backend|fullstack|full-stack", ctx):
                        continue
                seen.add((fam, low_phrase))
                if cv_has_exact_phrase(cv_hyphen, cv_joined, low_phrase):
                    covered_pairs.append((fam, low_phrase))
                else:
                    missing_pairs.append((fam, orig_phrase))

    jd_unknown = [k for k, rx in NEVER.items() if re.search(rx, jd_low)]
    cv_for_never = cv_hyphen.replace("azure fundamentals", "")
    cv_forbidden = [k for k, rx in NEVER.items() if re.search(rx, cv_for_never)]

    return {
        "missing_pairs": missing_pairs,
        "covered_pairs": covered_pairs,
        "missing": sorted({f"{p.lower()} [{fam}]" for fam, p in missing_pairs}),
        "covered": sorted({f"{p} [{fam}]" for fam, p in covered_pairs}),
        "jd_unknown": jd_unknown,
        "cv_forbidden": cv_forbidden,
    }


def main(jd_path: str, pdf_path: str) -> None:
    jd_raw = Path(jd_path).read_text(encoding="utf-8", errors="ignore")
    res = evaluate_jd_against_pdf(jd_raw, pdf_path)

    missing = res["missing"]
    covered = res["covered"]
    total = len(covered) + len(missing)

    print("MISSING (known skill, add JD's exact wording to CV):", "; ".join(missing) or "none")
    print("COVERED:", "; ".join(covered))
    print("JD asks for UNKNOWN skills (keep OUT of CV, list as Tier 3):", ", ".join(res["jd_unknown"]) or "none")
    print("FORBIDDEN-IN-CV:", ", ".join(res["cv_forbidden"]) or "none")
    print(f"COVERAGE: {len(covered)}/{total} = {100 * len(covered) // max(1, total)}%")
    if res["cv_forbidden"]:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
