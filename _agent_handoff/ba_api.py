"""Quick Bundesagentur fuer Arbeit (BA) multi-query REST API listing helper."""
import json
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
HANDOFF = Path(__file__).resolve().parent
H = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Mozilla/5.0"}
days = sys.argv[1] if len(sys.argv) > 1 else "14"
qs = [
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
    "Next.js Developer",
    "Full Stack Developer",
]
jobs = {}
for q in qs:
    for page in range(1, 5):
        r = requests.get(
            "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs",
            params={"was": q, "veroeffentlichtseit": days, "size": 100, "page": page, "angebotsart": 1},
            headers=H,
            timeout=30,
        )
        if r.status_code != 200:
            print("ERR", q, r.status_code)
            break
        st = r.json().get("ergebnisliste", [])
        for j in st:
            loc = (j.get("stellenlokationen") or [{}])[0].get("adresse", {}).get("ort", "")
            jobs[j["referenznummer"]] = dict(
                title=j.get("stellenangebotsTitel"),
                company=j.get("firma"),
                loc=loc,
                age=j.get("datumErsteVeroeffentlichung"),
                url="https://www.arbeitsagentur.de/jobsuche/jobdetail/" + j["referenznummer"],
                ext=j.get("externeUrl", ""),
            )
        if len(st) < 100:
            break
out_path = HANDOFF / "_ba_out.json"
out_path.write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(jobs))
