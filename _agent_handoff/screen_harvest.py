r"""
Live-Deduplicated Multi-Portal Harvest Screener (`_agent_handoff/screen_harvest.py`)
Reads `Application_Tracker.xlsx` + `Manual_Apply_Queue.xlsx` + workspace folders + `candidate_profile.json` live.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ats_poll import RED_TITLE, is_dup_company, load_known_company_keys, norm  # noqa: E402

new_path = sys.argv[1]
old_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
new = json.loads(Path(new_path).read_text(encoding="utf-8"))
old = json.loads(Path(old_path).read_text(encoding="utf-8")) if old_path and Path(old_path).exists() else {"fast_apis": {}, "german_portals": {}}

known_keys = load_known_company_keys()

EXTRA_PORTAL_NOISE = re.compile(
    r"\bsachbearbeit|\bkaufm|\bmitarbeiter.*(lager|logistik|pflege|empfang)|\btechniker\b|\belektroniker|"
    r"\bmechaniker|\bmechatroniker|\bbauleiter|\barchitekt\s*\(hochbau|\bsteuerfach|\bbuchhalt|\bpflege",
    re.I,
)
JOB_URL = re.compile(
    r"stellenangebote--|/job/|/jobs/|/rc/clk|viewjob|/jobs/view|jobdetail|/stellenangebot|/details|"
    r"/job-|/stelle/|/jobposting|/position|join\.com/companies/|ashbyhq\.com/|greenhouse\.io/|"
    r"lever\.co/|personio\.|workable\.com/|recruitee\.com/|smartrecruiters\.com/|teamtailor\.com/|"
    r"wearedevelopers\.com/en/jobs/|englishjobs\.de/(?:jobs|clickout)|get-in-it\.de/jobsuche/p",
    re.I,
)

oldurls = set()
for v in old.get("fast_apis", {}).values():
    if isinstance(v, list):
        oldurls |= {x.get("url") for x in v if isinstance(x, dict) and x.get("url")}
for v in old.get("german_portals", {}).values():
    if isinstance(v, list):
        oldurls |= {x.get("href") or x.get("url") for x in v if isinstance(x, dict) and (x.get("href") or x.get("url"))}

rows = []
for src, v in new.get("fast_apis", {}).items():
    if not isinstance(v, list):
        continue
    for x in v:
        if isinstance(x, dict) and x.get("url"):
            rows.append((src, x.get("company", ""), x.get("title", ""), x.get("location", ""), x["url"]))

for src, v in new.get("german_portals", {}).items():
    if not isinstance(v, list):
        continue
    for x in v:
        if not isinstance(x, dict):
            continue
        h = x.get("href") or x.get("url") or ""
        t = (x.get("title") or x.get("text") or "").strip()
        c = (x.get("company") or "").strip()
        loc = (x.get("location") or x.get("loc") or "").strip()
        if not h or not JOB_URL.search(h) or len(t) < 6:
            continue
        rows.append((src, c, re.sub(r"\s+", " ", t)[:200], loc, h))

seen = set()
for src, c, t, l, u in rows:
    u_clean = u.split("#")[0]
    if u_clean in seen:
        continue
    seen.add(u_clean)
    isnew = u_clean not in oldurls and u not in oldurls
    dup = is_dup_company(c, known_keys) if c else any(len(k) >= 6 and k in norm(t) for k in known_keys)
    red = bool(RED_TITLE.search(t) or EXTRA_PORTAL_NOISE.search(t))
    tag = "DUP" if dup else ("RED" if red else "NEW")
    if "--all" in sys.argv or (isnew and tag == "NEW"):
        print(f"{tag} | {src} | {c} | {t} | {l} | {u_clean[:180]}")
