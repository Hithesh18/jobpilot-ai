r"""
Unified Zero-CAPTCHA Multi-ATS & Tech-Feed Poller (`_agent_handoff/ats_poll.py`)
Usage:
  python _agent_handoff/ats_poll.py [slugs_file_or_-] [days=14] [--json out.json]

Polls BOTH:
  A) Global Feeds (catches ANY company in target region, zero slug needed):
     1. Workable Global API (`jobs.workable.com/api/v1/jobs`) across 12 stack/role queries
     2. GermanTechJobs Full XML RSS (`germantechjobs.de/rss`)
     3. BerlinStartupJobs Engineering RSS (`berlinstartupjobs.com/engineering/feed/`)
     4. Arbeitnow JSON API (`arbeitnow.com/api/job-board-api`, pages 1-3)
  B) Company-Slug Public APIs (Ashby, Greenhouse, Lever, Recruitee, SmartRecruiters, Personio)

Automatically deduplicates against `Application_Tracker.xlsx` + `Manual_Apply_Queue.xlsx` + workspace folders + `candidate_profile.json`.
"""
import datetime as dt
import email.utils
import json
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")

HANDOFF = Path(__file__).resolve().parent
ROOT = HANDOFF.parent
sys.path.insert(0, str(HANDOFF))
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
TARGET_COUNTRY = PROF.get("targeting", {}).get("target_country", "Germany")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"}

DE = re.compile(
    r"germany|deutschland|berlin|munich|münchen|muenchen|hamburg|cologne|köln|koeln|frankfurt|stuttgart|"
    r"düsseldorf|duesseldorf|leipzig|dresden|karlsruhe|nuremberg|nürnberg|hannover|bonn|mannheim|aachen|"
    r"heidelberg|freiburg|ulm|walldorf|darmstadt|potsdam|augsburg|remote.*(eu|europe|germany|dach|emea)|"
    r"(eu|europe|germany|dach)\s*remote|\bdach\b",
    re.I,
)
REL = re.compile(
    r"junior|mid[- ]?level|associate|graduate|entry[- ]level|full.?stack|front.?end|back.?end|"
    r"typescript|javascript|react|vue|next\.?js|node\.?js|nestjs|web developer|web engineer|"
    r"ui engineer|3d|webgl|three\.?js|ai engineer|applied ai|genai|llm|software engineer|"
    r"software developer|application developer",
    re.I,
)
# ZERO-REJECTION SENIORITY & STACK GATE:
# Hard-blocks bare `Senior` (while allowing `(Senior)` in parens to be checked for 2-4 YOE + open-to-mid),
# plus `Staff`, `Principal`, `Lead`, `Founding`, `Forward Deployed`, `Solutions Engineer`, `Consultant`, `Data Platform`, etc.
RED_TITLE = re.compile(
    r"(?<!\()\bsenior\b(?!\))|\bsr\.?\s|\bstaff\b|\bprincipal\b|\blead\b|\bteam.?lead\b|\bchapter lead\b|"
    r"\bhead of\b|\bdirector\b|\bvp\b|\bvice president\b|\barchitect\b|\bmanager\b|"
    r"\bfounding\b|\bco-?founder\b|\bforward deployed\b|\bsolutions? engineer\b|\bconsultant\b|\bberater\b|"
    r"\bdata platform\b|\bdata engineer\b|\bdata lake\b|\bdata scien|\bmlops\b|\bsre\b|\bdevops engineer\b|"
    r"\bjava\b|\bspring boot\b|\.net\b|\bc#|\bphp\b|\blaravel\b|\bsymfony\b|\bgolang\b|\bgo engineer\b|\bgo developer\b|"
    r"\brust\b|\bc\+\+|\bembedded\b|\bfirmware\b|\bandroid\b|\bios\b|\bswift\b|\bkotlin\b|\bflutter\b|\breact native\b|"
    r"\bruby\b|\brails\b|\bscala\b|\bsap\b|\babap\b|\bsalesforce\b|\bservicenow\b|\bodoo\b|\bmendix\b|\bdynamics 365\b|"
    r"\bwerkstudent|\bworking student|\bintern\b|\binternship|\bpraktik|\bausbildung|\bduales|\bthesis\b|\bmasterarbeit|"
    r"\(python\)|\bpython (?:developer|engineer|backend)|\bbackend (?:developer|engineer) python|\bsales\b|\baccount executive|\brecruiter|\bmarketing|\bfinance\b|\blegal\b|\bhr\b|\bcustomer success",
    re.I,
)
GERMAN_BODY_RED = re.compile(
    # Requirement-only: German-WRITTEN JDs are NOT auto-red; only mandatory B1+ / good/fluent German demands are.
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
    r"\bdeutsch(?:\s+und\s+englisch)?\s+(?:sehr\s+gut|gut|flie(?:ß|ss)end|sicher|verhandlungssicher)\s+beherrsch\w*|\bdeutsch\w*[^.!?\n]{0,65}\b(?:mind(?:estens|\.)?\s+)?(?:auf\s+)?(?:b1|b2|c1|c2)[\s-]*niveau|"
    r"\b(?:[5-9]|1\d)\+\s*(?:years|yrs)\s+(?:of\s+)?(?:professional\s+|full[- ]time\s+)?(?:experience|software|engineering|development)",
    re.I,
)
HARD_YOE_WORDS = re.compile(
    r"\b(?:mindestens\s+|min\.\s*|at least\s+)?(?:fünf|sechs|sieben|acht|neun|zehn|five|six|seven|eight|nine|ten)\+?\s+(?:jahre|years)",
    re.I,
)
GERMAN_OK_CTX = re.compile(
    r"plus|nice to have|nice-to-have|advantage|bonus|beneficial|optional|not required|helpful|preferred|"
    r"von vorteil|wünschenswert|wuenschenswert|vorteilhaft|gerne gesehen|ein plus|kein muss|keinesfalls|nicht erforderlich",
    re.I,
)


def german_requirement(text: str):
    """Return the matched German-requirement phrase (with context) if German is REQUIRED, else None."""
    for m in GERMAN_BODY_RED.finditer(text or ""):
        if re.match(r"\d", m.group(0)):
            continue
        if "ausreichend" in m.group(0).lower():
            return text[max(0, m.start() - 60) : m.end() + 30].strip()
        before = text[max(0, m.start() - 160) : m.start()]
        after = text[m.end() : m.end() + 70]
        after = re.split(
            r"\s(?:Nice[- ]to[- ][Hh]ave|Benefits|Das bieten|Wir bieten|Was wir bieten|Unser Angebot|What we offer|Bonus|Zusätzliche Pluspunkte|Pluspunkte|Darüber hinaus|Außerdem von Vorteil|Folgende Kenntnisse|Folgendes ist|Wünschenswert|Wuenschenswert|Nice to Have)\b|\*\*|\s[Vv]on [Vv]orteil:|(?:[,;]|\s(?:sowie|und|and|as well as))\s*(?:\w+\s+){0,2}(?:Englisch|English)",
            after,
        )[0]
        hdr = list(re.finditer(r"(?:^|\n)\s*(?:Nice[- ]to[- ]have|Wünschenswert|Von Vorteil|Plus|Bonus|Optional)\s*:?\s*(?:\n|$)", before, re.I))
        req_hdr = list(
            re.finditer(
                r"(?:Dein Profil|Das bringst du mit|Was du mitbringst|Anforderungen|Requirements|Must[- ]haves?|Qualifikation|Your profile|What you bring)",
                before,
                re.I,
            )
        )
        in_optional_section = bool(hdr) and (not req_hdr or hdr[-1].start() > req_hdr[-1].start())
        inline_hdr = list(re.finditer(r"(?:nice[- ]to[- ]have|wünschenswert|von vorteil|pluspunkte|bonus|optional)\s*:", before, re.I))
        if inline_hdr and "\n" not in before[inline_hdr[-1].end() :] and (not req_hdr or inline_hdr[-1].start() > req_hdr[-1].start()):
            in_optional_section = True
        prefix_ok = re.search(
            r"(?:von vorteil|wünschenswert|nice[- ]to[- ]have|ein plus|ein \"?plus\"?|plus|bonus|optional|gerne gesehen)\s*(?::|sind|ist|wären|wäre|w\u00e4ren)\s*$",
            before[-35:].lower(),
        )
        if in_optional_section or GERMAN_OK_CTX.search(m.group(0) + after) or prefix_ok:
            continue
        return (before[-60:] + m.group(0) + after).strip()
    return None


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def core_company(c: str) -> str:
    cleaned = re.sub(
        r"\b(gmbh|se|ag|inc|ltd|llc|ug|co|kg|technologies|technology|tech|software|solutions|group|mbh|holding|deutschland|germany|hq|ai|io|labs)\b",
        "",
        (c or "").lower(),
    )
    return norm(cleaned)


def load_known_company_keys() -> set[str]:
    do_not_apply = PROF.get("targeting", {}).get("permanent_do_not_apply", [])
    keys = {norm(x) for x in do_not_apply if len(norm(x)) >= 4}
    for emp in PROF.get("employers", {}).values():
        if isinstance(emp, dict) and emp.get("name"):
            for k in (norm(emp["name"]), core_company(emp["name"])):
                if len(k) >= 4:
                    keys.add(k)

    for xlsx_name in ("Application_Tracker.xlsx", "Manual_Apply_Queue.xlsx"):
        p = ROOT / xlsx_name
        if not p.exists():
            continue
        try:
            wb = load_workbook(p, read_only=True)
            ws = wb.active
            for r in ws.iter_rows(min_row=2, values_only=True):
                comp = str(r[1] or "").strip()
                if len(comp) >= 2:
                    for k in (norm(comp), core_company(comp)):
                        if len(k) >= 4:
                            keys.add(k)
                for cell in r:
                    if isinstance(cell, str) and "http" in cell:
                        m = re.search(
                            r"(?:ashbyhq\.com|greenhouse\.io|lever\.co|smartrecruiters\.com|join\.com/companies)/([^/?#]+)|([^/.]+)\.(?:jobs\.personio\.de|recruitee\.com|teamtailor\.com)",
                            cell,
                            re.I,
                        )
                        if m:
                            sl = norm(next((g for g in m.groups() if g), ""))
                            if len(sl) >= 4:
                                keys.add(sl)
            wb.close()
        except Exception:
            pass
    for d in ROOT.iterdir():
        if d.is_dir() and not d.name.startswith(("_", ".")):
            prefix = norm(d.name.split("_")[0])
            if len(prefix) >= 4:
                keys.add(prefix)
    return keys


def is_dup_company(company_or_slug: str, known_keys: set[str]) -> bool:
    n1 = norm(company_or_slug)
    n2 = core_company(company_or_slug)
    for cand in (n1, n2):
        if len(cand) >= 4 and cand in known_keys:
            return True
    for k in known_keys:
        if len(k) >= 6 and (n1.startswith(k) or n2.startswith(k)):
            return True
    return False


def parse_ts(x):
    if not x:
        return None
    try:
        if isinstance(x, (int, float)):
            val = x / 1000.0 if x > 1e11 else float(x)
            return dt.datetime.fromtimestamp(val, dt.timezone.utc)
        s = str(x).strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            return dt.datetime.fromisoformat(s + "T00:00:00+00:00")
        try:
            return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            parsed = email.utils.parsedate_to_datetime(s)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def load_slugs(arg_path: str) -> list[str]:
    slugs = set()
    candidates = []
    if arg_path and arg_path != "-" and Path(arg_path).exists():
        candidates.append(Path(arg_path))
    for fallback in (HANDOFF / "slugs_starter.txt", HANDOFF / "_slugs_all.txt"):
        if fallback.exists():
            candidates.append(fallback)
    for p in candidates:
        for tok in p.read_text(encoding="utf-8", errors="ignore").split():
            t = tok.strip().lower()
            if len(t) >= 2 and re.match(r"^[a-z0-9_-]+$", t):
                slugs.add(t)
    return sorted(slugs)


def poll_global_workable(days: int) -> list[tuple]:
    out = []
    day_range = 1 if days <= 1 else (3 if days <= 3 else (7 if days <= 7 else 14))
    queries = [
        "Junior Full Stack",
        "Junior Frontend",
        "Junior Software Engineer",
        "Mid-Level Full Stack",
        "React Developer",
        "Vue.js Developer",
        "TypeScript Developer",
        "Node.js Developer",
        "Web Developer",
        "Junior AI Engineer",
        "Full Stack Developer",
        "Next.js",
    ]
    seen_ids = set()
    for q in queries:
        next_tok = None
        for _ in range(3):
            params = {"location": TARGET_COUNTRY, "query": q, "day_range": day_range}
            if next_tok:
                params["pageToken"] = next_tok
            try:
                r = requests.get("https://jobs.workable.com/api/v1/jobs", params=params, headers=H, timeout=12)
                if not r.ok:
                    break
                data = r.json()
                for j in data.get("jobs", []):
                    jid = j.get("id")
                    if not jid or jid in seen_ids:
                        continue
                    seen_ids.add(jid)
                    comp = (j.get("company") or {}).get("title") or ""
                    loc_obj = j.get("location") or {}
                    loc = ", ".join(filter(None, [loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("countryName")]))
                    if j.get("workplace") == "remote":
                        loc = f"{loc} (Remote)".strip()
                    desc = j.get("description") or ""
                    if GERMAN_BODY_RED.search(desc):
                        continue
                    out.append(("workable", comp, j.get("title") or "", loc, parse_ts(j.get("created")), j.get("url") or ""))
                next_tok = data.get("nextPageToken")
                if not next_tok:
                    break
            except Exception:
                break
    return out


def poll_rss_feeds(cut: dt.datetime) -> list[tuple]:
    out = []
    # 1. GermanTechJobs RSS
    try:
        r = requests.get("https://germantechjobs.de/rss", headers=H, timeout=20)
        if r.ok:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title_raw = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = parse_ts(item.findtext("pubDate"))
                desc = item.findtext("description") or ""
                if pub and pub < cut:
                    continue
                if GERMAN_BODY_RED.search(desc):
                    continue
                comp = ""
                title = title_raw
                loc = "Germany"
                m_at = re.match(r"^(.*?)\s+@\s+([^\[\(]+)", title_raw)
                m = re.match(r"^(.*?)\s+at\s+([^\(]+)(?:\((.*?)\))?$", title_raw)
                if m_at:
                    title, comp = m_at.group(1).strip(), m_at.group(2).strip()
                elif m:
                    title, comp, loc = m.group(1).strip(), m.group(2).strip(), (m.group(3) or "Germany").strip()
                out.append(("germantechjobs", comp, title, loc, pub, link))
    except Exception:
        pass

    # 2. BerlinStartupJobs Engineering RSS
    try:
        r = requests.get("https://berlinstartupjobs.com/engineering/feed/", headers=H, timeout=15)
        if r.ok:
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title_raw = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = parse_ts(item.findtext("pubDate"))
                desc = item.findtext("description") or ""
                if pub and pub < cut:
                    continue
                if GERMAN_BODY_RED.search(desc):
                    continue
                comp = ""
                if "//" in title_raw:
                    parts = title_raw.split("//", 1)
                    title_raw, comp = parts[0].strip(), parts[1].strip()
                out.append(("berlinstartupjobs", comp, title_raw, "Berlin, Germany", pub, link))
    except Exception:
        pass

    # 3. Arbeitnow JSON API (pages 1-3)
    for page in (1, 2, 3):
        try:
            r = requests.get(f"https://www.arbeitnow.com/api/job-board-api?page={page}", headers=H, timeout=12)
            if not r.ok:
                break
            items = r.json().get("data", [])
            if not items:
                break
            for j in items:
                pub = parse_ts(j.get("created_at"))
                if pub and pub < cut:
                    continue
                desc = j.get("description") or ""
                if GERMAN_BODY_RED.search(desc):
                    continue
                loc = j.get("location") or "Germany"
                if j.get("remote"):
                    loc += " (Remote Germany)"
                out.append(("arbeitnow", j.get("company_name") or "", j.get("title") or "", loc, pub, j.get("url") or ""))
        except Exception:
            break

    return out


def poll_company_slug(s: str) -> tuple[str, list[tuple]]:
    out = []
    # 1. Ashby
    try:
        r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{s}", headers=H, timeout=8)
        if r.ok:
            for j in r.json().get("jobs", []):
                loc = " ".join([str(j.get("location") or "")] + [str(x.get("location") or "") for x in j.get("secondaryLocations", [])])
                out.append(("ashby", s, j.get("title") or "", loc, parse_ts(j.get("publishedAt")), j.get("jobUrl") or ""))
    except Exception:
        pass
    # 2. Greenhouse
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs", headers=H, timeout=8)
        if r.ok:
            for j in r.json().get("jobs", []):
                loc = (j.get("location") or {}).get("name") or ""
                out.append(("greenhouse", s, j.get("title") or "", loc, parse_ts(j.get("first_published") or j.get("updated_at")), j.get("absolute_url") or ""))
    except Exception:
        pass
    # 3. Lever
    try:
        r = requests.get(f"https://api.lever.co/v0/postings/{s}?mode=json", headers=H, timeout=8)
        if r.ok and isinstance(r.json(), list):
            for j in r.json():
                cats = j.get("categories") or {}
                loc = " ".join([cats.get("location") or ""] + (cats.get("allLocations") or []))
                desc = j.get("descriptionPlain") or ""
                if GERMAN_BODY_RED.search(desc):
                    continue
                out.append(("lever", s, j.get("text") or "", loc, parse_ts(j.get("createdAt")), j.get("hostedUrl") or ""))
    except Exception:
        pass
    # 4. Recruitee
    try:
        r = requests.get(f"https://{s}.recruitee.com/api/offers", headers=H, timeout=6)
        if r.ok:
            for j in r.json().get("offers", []):
                loc = " ".join(filter(None, [j.get("location"), j.get("country"), "Remote" if j.get("remote") else ""]))
                desc = (j.get("description") or "") + " " + (j.get("requirements") or "")
                if GERMAN_BODY_RED.search(desc):
                    continue
                out.append(("recruitee", s, j.get("title") or "", loc, parse_ts(j.get("published_at") or j.get("created_at")), j.get("careers_url") or ""))
    except Exception:
        pass
    # 5. SmartRecruiters
    try:
        r = requests.get(f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=100", headers=H, timeout=6)
        if r.ok:
            for j in r.json().get("content", []):
                loc_obj = j.get("location") or {}
                loc = " ".join(
                    filter(
                        None,
                        [
                            loc_obj.get("city"),
                            loc_obj.get("country"),
                            "Germany" if loc_obj.get("country") == "de" else "",
                            "Remote" if loc_obj.get("remote") else "",
                        ],
                    )
                )
                jid = j.get("id") or ""
                url = f"https://jobs.smartrecruiters.com/{s}/{jid}" if jid else ""
                out.append(("smartrecruiters", s, j.get("name") or "", loc, parse_ts(j.get("releasedDate")), url))
    except Exception:
        pass
    # 6. Personio
    try:
        r = requests.get(f"https://{s}.jobs.personio.de/search.json", headers=H, timeout=6)
        if r.ok and isinstance(r.json(), list):
            for j in r.json():
                jid = j.get("id")
                office = j.get("office") or ""
                loc = " ".join(filter(None, [office, j.get("department")]))
                url = f"https://{s}.jobs.personio.de/job/{jid}?language=en" if jid else ""
                out.append(("personio", s, j.get("name") or "", loc, None, url))
    except Exception:
        pass
    return s, out


def main():
    slug_arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "-"
    days = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 14
    include_dups = "--include-dups" in sys.argv
    cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)

    known_keys = load_known_company_keys()
    slugs = load_slugs(slug_arg)

    all_raw = []
    all_raw.extend(poll_global_workable(days))
    all_raw.extend(poll_rss_feeds(cut))

    boards_found = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(poll_company_slug, s) for s in slugs]
        for fut in as_completed(futures):
            _, items = fut.result()
            if items:
                boards_found += 1
                all_raw.extend(items)

    hits = []
    seen_urls = set()
    for src, comp, title, loc, pub, url in all_raw:
        if not url or url in seen_urls:
            continue
        if not DE.search(loc):
            continue
        if not REL.search(title):
            continue
        if RED_TITLE.search(title):
            continue
        if pub is not None and pub < cut:
            continue
        if pub is None and days <= 1:
            continue
        if not include_dups and is_dup_company(comp, known_keys):
            continue
        seen_urls.add(url)
        date_str = pub.date().isoformat() if pub else "14d-undated"
        hits.append(
            {
                "date": date_str,
                "source": src,
                "company": comp,
                "title": title.strip(),
                "location": re.sub(r"\s+", " ", loc).strip()[:65],
                "url": url,
            }
        )

    hits.sort(key=lambda x: (x["date"], x["source"]), reverse=True)
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        out_path = Path(sys.argv[idx + 1])
        out_path.write_text(json.dumps(hits, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"slugs_polled={len(slugs)} active_company_boards={boards_found} fresh_unseen_hits={len(hits)} (days={days})")
    for h in hits:
        print(f"{h['date']} | {h['source']} | {h['company']} | {h['title']} | {h['location']} | {h['url']}")


if __name__ == "__main__":
    main()
