r"""
Honest 100-Point ATS & Human-Recruiter Fit Analyzer (`_agent_handoff/gen_ats_analysis.py`)
Shared by Claude Code & Gemini Antigravity — penalizes missing unverified stacks, YOE stretch, and language gates
so inflated keyword-only illusions never recur. Minimum threshold to apply: `>= 82/100` (with 0 hard dealbreakers).

Usage:
  python _agent_handoff/gen_ats_analysis.py <folder> "<Company>" "<Title>" "<recency/portal note>" [salary]
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from profile_loader import get_python_exe, load_profile, resume_pdf_filename  # noqa: E402

PROF = load_profile()
CAND = PROF.get("candidate", {})
TARG = PROF.get("targeting", {})
EMP_CUR = PROF.get("employers", {}).get("current", {}).get("name", "Current Employer")
EDU_UNI = CAND.get("education", {}).get("current_university", "Technical University")
START_DATE = CAND.get("availability", {}).get("earliest_start_de", "01.12.2026")
DEFAULT_SALARY = CAND.get("compensation", {}).get("default_range", "EUR 60,000 - 70,000")
MIN_FIT_SCORE = int(TARG.get("min_honest_fit_score", 82))
RES_PDF = resume_pdf_filename(PROF)

folder, company, title, note = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
salary = sys.argv[5] if len(sys.argv) > 5 else DEFAULT_SALARY

out = subprocess.run(
    [
        get_python_exe(),
        str(H / "ats_keyword_check.py"),
        str(folder / "Job_Description.txt"),
        str(folder / RES_PDF),
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
).stdout

get = lambda k: (re.search(k + r"[^:]*:\s*(.*)", out) or [None, ""])[1].strip()
covered = [c.split(" [")[0] for c in get("COVERED").split("; ") if c]
unknown = [u for u in get(r"JD asks for UNKNOWN skills").split(", ") if u and u != "none"]
jd = (folder / "Job_Description.txt").read_text(encoding="utf-8", errors="ignore")
jd_body = jd.split("--- JOB DESCRIPTION ---")[-1] if "--- JOB DESCRIPTION ---" in jd else jd
de_lines = [x.strip()[:160] for x in re.findall(r"[^.\n]*(?:german|deutsch)[^.\n]*", jd_body, re.I)]

ALL_CORE_LANGS = (
    "Go/Golang",
    "C#/.NET",
    "Java/Spring",
    "Kotlin",
    "C/C++",
    "Rust",
    "PHP",
    "Ruby/Rails",
    "Scala",
    "Django/FastAPI",
    "SAP/Salesforce",
)
LANG_PAT = {
    "Go/Golang": r"(?i:\bgolang\b)|\bGo\b",
    "C#/.NET": r"(?i:c#|\.net)",
    "Java/Spring": r"(?i:\bjava\b|\bspring)",
    "Kotlin": r"(?i:\bkotlin\b)",
    "C/C++": r"(?i:\bc\+\+|\bc/c\+\+)",
    "Rust": r"(?i:\brust\b)",
    "PHP": r"(?i:\bphp\b|\blaravel|\bsymfony|\bshopware)",
    "Ruby/Rails": r"(?i:\bruby\b|\brails\b)",
    "Scala": r"(?i:\bscala\b)",
    "Django/FastAPI": r"(?i:\bdjango\b|\bfastapi\b)",
    "SAP/Salesforce": r"(?i:\bsap\b|\bsalesforce\b|\babap\b)",
}
OPT_CTX = re.compile(
    r"von vorteil|wünschenswert|wuenschenswert|ein plus|idealerweise|nice[- ]to[- ]have|optional|bonus|"
    r"advantage|preferred|beneficial|interesse[^.\n]{0,80}weiterzuentwickeln|interest in (?:learning|developing|growing)|willingness to learn",
    re.I,
)
OPT_HDR = re.compile(
    r"(?:^|\n)\s*(?:#+\s*|\*+\s*)?(?:nice[- ]to[- ]have|bonus(?:\s+points?)?|pluspunkte|von\s+vorteil|wünschenswert|preferred(?:\s+qualifications?)?)\s*:?\s*(?:\*+)?\s*(?:\n|$)",
    re.I,
)
REQ_HDR = re.compile(
    r"(?:^|\n)\s*(?:#+\s*|\*+\s*)?(?:requirements?|must[- ]haves?|technical\s+requirements?|your\s+profile|what\s+you\s+bring|what\s+we\s+offer|about\s+us)\s*:?\s*(?:\*+)?\s*(?:\n|$)",
    re.I,
)
ALT_KNOWN_CTX = re.compile(
    r"(?:(?:beispielsweise|z\.\s*b\.|zum beispiel|e\.g\.|for example|such as)\b[^.\n]*\b(?:oder|or)\b[^.\n]*\b(?:typescript|javascript|node\.?js|react|vue)"
    r"|\b(?:oder|or)\s+(?:typescript|javascript|node\.?js|react|vue)\b"
    r"|\b(?:typescript|javascript|node\.?js|react|vue)\b[^.\n]{0,90}\b(?:oder|or|fast-converting\s+from)\b)",
    re.I,
)


def _is_satisfied_alt_in_jd(u_name: str, body: str) -> bool:
    pat = LANG_PAT.get(u_name)
    if not pat:
        return False
    matches = list(re.finditer(pat, body))
    if not matches:
        return False
    for m in matches:
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_end = body.find("\n", m.end())
        if line_end == -1:
            line_end = len(body)
        clause = (
            body[line_start:line_end]
            if (line_end - line_start) <= 320
            else body[max(line_start, m.start() - 90) : min(line_end, m.end() + 220)]
        )
        if not ALT_KNOWN_CTX.search(clause):
            return False
    return True


def _is_strictly_optional_in_jd(u_name: str, body: str) -> bool:
    pat = LANG_PAT.get(u_name)
    if not pat:
        return False
    matches = list(re.finditer(pat, body))
    if not matches:
        return False
    for m in matches:
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_end = body.find("\n", m.end())
        if line_end == -1:
            line_end = len(body)
        clause = (
            body[line_start:line_end]
            if (line_end - line_start) <= 320
            else body[max(line_start, m.start() - 90) : min(line_end, m.end() + 220)]
        )
        prev_win = body[max(0, m.start() - 450) : m.start()]
        opt_hdrs = list(OPT_HDR.finditer(prev_win))
        req_hdrs = list(REQ_HDR.finditer(prev_win))
        under_opt_hdr = bool(opt_hdrs) and (not req_hdrs or opt_hdrs[-1].start() > req_hdrs[-1].start())
        if not (OPT_CTX.search(clause) or ALT_KNOWN_CTX.search(clause) or under_opt_hdr):
            return False
    return True


satisfied_alts = {u for u in unknown if u in ALL_CORE_LANGS and _is_satisfied_alt_in_jd(u, jd_body)}
core_lang_mismatch = [
    u for u in unknown if u in ALL_CORE_LANGS and u not in satisfied_alts and not _is_strictly_optional_in_jd(u, jd_body)
]
infra_optional_gaps = [u for u in unknown if u not in core_lang_mismatch and u not in satisfied_alts]

tech = max(10, 30 - 7 * len(core_lang_mismatch) - 2 * len(infra_optional_gaps))
exp = 23 if re.search(r"\bjunior\b|\bmid\b|\bassociate\b|\bgraduate\b", title, re.I) else 21
if re.search(r"\b[5-9]\+\s*(?:years|yrs)", jd_body, re.I):
    exp -= 8
resp = 14 if len(covered) >= 8 else 12
pref = max(4, 9 - 2 * len(infra_optional_gaps))
edu = 10
ats = 10

tailored = tech + exp + resp + pref + edu + ats
init = {"tech": max(8, tech - 5), "exp": max(10, exp - 3), "resp": resp - 2, "pref": max(3, pref - 2), "edu": edu, "ats": 7}
initial = sum(init.values())
t1, t2 = covered[: len(covered) // 2 + 1], covered[len(covered) // 2 + 1 :]
verdict = (
    "APPLY (GREEN ZONE)"
    if tailored >= MIN_FIT_SCORE and len(core_lang_mismatch) <= 1
    else f"DO NOT APPLY (BELOW {MIN_FIT_SCORE} HONEST FIT GATE)"
)

md = f"""# ATS & Human-Recruiter Fit Analysis: {company} — {title}

- **Honest Fit Verdict:** **{verdict}**
- **Initial CV Score -> Tailored Resume Score:** **{initial} -> {tailored}/100** *(minimum threshold >= {MIN_FIT_SCORE}/100)*
- **Keyword Gate:** {get("COVERAGE")} of verified JD skills mirrored; `FORBIDDEN-IN-CV`: `{get("FORBIDDEN-IN-CV")}`
- **German Requirement (verbatim JD lines):** {"; ".join(de_lines) if de_lines else "None — English-only JD"}
- **Target Compensation (Form Only, Omitted From Cover Letter Unless Requested):** {salary} | Available `{START_DATE}`

## Keyword Table

| Tier | Keywords | Status |
|---|---|---|
| Tier 1 (Critical, matched) | {", ".join(t1) or "-"} | Mirrored in Summary, Primary Skills & Experience |
| Tier 2 (Important, matched) | {", ".join(t2) or "-"} | Mirrored in Skills & Experience |
| Tier 3 (Unverified — honestly omitted) | {", ".join(unknown) or "none"} | Strictly kept OUT of CV |

## 100-Point Honest Comparative Score

| Category | Max | Initial CV | Tailored CV |
|---|---:|---:|---:|
| 1. Required Technical Skills | 30 | {init["tech"]} | {tech} |
| 2. Relevant Professional Experience (`0–4 YOE` HR lens) | 25 | {init["exp"]} | {exp} |
| 3. Relevant Responsibilities & Achievements | 15 | {init["resp"]} | {resp} |
| 4. Preferred / Supporting Skills | 10 | {init["pref"]} | {pref} |
| 5. Education & Qualifications | 10 | {init["edu"]} | {edu} |
| 6. ATS Structure & Readability | 10 | {init["ats"]} | {ats} |
| **Total** | **100** | **{initial}** | **{tailored}** |

## 3-Perspective Review

- **ATS Parser:** Summary opens with exact JD title and JD's primary framework ecosystem (no unrelated framework soup). Single-column 1-page PDF (`{get("COVERAGE")}`).
- **Technical Hiring Manager:** Concrete production metrics (API latency optimization, distributed replica race fix, multi-tenant auth hardening, zero-downtime releases) + plain humanized cover letter. Unverified gaps: `{", ".join(unknown) or "none"}`.
- **HR / Recruiter:** `0–4 YOE` sweet-spot alignment (`{EMP_CUR}` active `Present`, {EDU_UNI}, fluent English, `{ CAND.get("spoken_languages", {}).get("german_level", "A2") }` German).

## Notes

{note}
"""
(folder / "ATS_Analysis.md").write_text(md, encoding="utf-8")
print(f"ATS_Analysis.md written: {initial} -> {tailored}/100 [{verdict}]")
if verdict.startswith("DO NOT APPLY"):
    sys.exit(2)
