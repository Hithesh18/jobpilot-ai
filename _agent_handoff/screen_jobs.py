"""Screen an arbitrary JSON list/dict of scraped job postings against live tracker & Red-Zone title rules."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ats_poll import RED_TITLE, is_dup_company, load_known_company_keys  # noqa: E402

jobs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if isinstance(jobs, dict):
    jobs = list(jobs.values())
keys = load_known_company_keys()

for j in jobs:
    c = j.get("company", "") or ""
    dup = is_dup_company(c, keys) if c else False
    red = bool(RED_TITLE.search(j.get("title", "") or ""))
    tag = "DUP" if dup else ("RED" if red else "NEW")
    print(tag, "|", c, "|", j.get("title"), "|", j.get("loc", ""), "|", j.get("age", ""), "|", j.get("jk") or j.get("url", ""))
