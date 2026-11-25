r"""
Live-Deduplicated Search-Engine ATS Dork Screener (`_agent_handoff/screen_google.py`)
Reads `Application_Tracker.xlsx` + `Manual_Apply_Queue.xlsx` + workspace folders + `candidate_profile.json` live.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")
HANDOFF = Path(__file__).resolve().parent
sys.path.insert(0, str(HANDOFF))
from ats_poll import RED_TITLE, is_dup_company, load_known_company_keys  # noqa: E402

in_file = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else str(HANDOFF / "_sp_out.json")
out = json.loads(Path(in_file).read_text(encoding="utf-8"))
known_keys = load_known_company_keys()

SEARCH_ENGINE_HOSTS = re.compile(
    r"(startpage\.com|ixquick\.com|yahoo\.com|brave\.com|google\.|bing\.com|duckduckgo\.com|msn\.com)$",
    re.I,
)

seen = set()
for x in out:
    raw_u = (x.get("u") or "").strip()
    if not raw_u:
        continue
    try:
        host = urlparse(raw_u).hostname or ""
    except Exception:
        continue
    if not host or SEARCH_ENGINE_HOSTS.search(host):
        continue
    u = raw_u.split("?")[0].rstrip("/")
    if u in seen:
        continue
    seen.add(u)

    m = re.search(
        r"ashbyhq\.com/([^/]+)|greenhouse\.io/([^/]+)|lever\.co/([^/]+)|"
        r"([^/.]+)\.jobs\.personio\.(?:de|com)|workable\.com/(?:view/[^/]+/|([^/]+))|"
        r"([^/.]+)\.recruitee\.com|smartrecruiters\.com/([^/]+)|"
        r"([^/.]+)\.teamtailor\.com|join\.com/companies/([^/]+)",
        u,
        re.I,
    )
    slug = next((g for g in (m.groups() if m else []) if g), "") if m else ""
    if not slug:
        slug = host.split(".")[0]

    title_or_slug = (x.get("t") or "").strip() or u.split("/")[-1].replace("-", " ")
    snippet = (x.get("s") or "").strip()
    dup = is_dup_company(slug, known_keys)
    tag = "DUP" if dup else ("RED" if RED_TITLE.search(title_or_slug) else "NEW")
    if "--all" in sys.argv or tag == "NEW":
        print(f"{tag} | {slug} | {title_or_slug[:110]} | {u[:140]} | {snippet[:160]}")
