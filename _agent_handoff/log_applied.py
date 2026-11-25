r"""
Log a NEW submitted application (picks the next free APP-ID at write time, so concurrent agents never collide).
Usage: python _agent_handoff/log_applied.py <job_folder> "<posting_url>" "<apply_url>" "<required_experience>" "<notes>" [status=Applied]
Reads spec.json (company/title/location/salary) + ATS_Analysis.md (tailored score) from the folder.
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from profile_loader import cover_letter_pdf_filename, load_profile, resume_pdf_filename  # noqa: E402
from update_tracker_batch import DEFAULT_TRACKER_PATH, upsert_application  # noqa: E402

PROF = load_profile()
RES_NAME = resume_pdf_filename(PROF)
CL_NAME = cover_letter_pdf_filename(PROF)
COUNTRY = PROF.get("targeting", {}).get("target_country", "Germany")
CURRENCY = PROF.get("candidate", {}).get("compensation", {}).get("currency", "EUR")
DEFAULT_SAL = PROF.get("candidate", {}).get("compensation", {}).get("default_number", "65,000")
AGENT = os.environ.get("AGENT_NAME", "Claude")

folder = Path(sys.argv[1])
posting, apply_url, exp, notes = sys.argv[2:6]
status = sys.argv[6] if len(sys.argv) > 6 else "Applied"
spec = json.loads((folder / "spec.json").read_text(encoding="utf-8-sig"))
ats = (folder / "ATS_Analysis.md").read_text(encoding="utf-8") if (folder / "ATS_Analysis.md").exists() else ""
m = re.search(r"->\s*\**(\d+)/100", ats)
score = int(m.group(1)) if m else ""
jd = (folder / "Job_Description.txt").read_text(encoding="utf-8", errors="ignore")

ws = load_workbook(DEFAULT_TRACKER_PATH, read_only=True)["Applications"]
nums, companies = [0], set()
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] and str(r[0]).startswith("APP-"):
        nums.append(int(str(r[0])[4:]))
    if r[1]:
        companies.add(re.sub(r"[^a-z0-9]", "", str(r[1]).lower()))
if re.sub(r"[^a-z0-9]", "", spec["company"].lower()) in companies:
    raise SystemExit(f"STOP: {spec['company']} already in tracker (one company = one role)")
app = f"APP-{max(nums) + 1:03d}"
now = dt.datetime.now().astimezone()
today = now.strftime("%Y-%m-%d")
techs = ", ".join(
    sorted(
        set(
            re.findall(
                r"TypeScript|JavaScript|React|Vue\.js|Vue|Pinia|Vite|Tailwind CSS|Node\.js|NestJS|Express|Three\.js|WebGL|"
                r"react-three-fiber|PostgreSQL|MongoDB|Redis|Docker|Kubernetes|WebSockets|REST|LangChain|LangGraph|RAG",
                jd,
            )
        )
    )
)
row = [
    app,
    spec["company"],
    spec["title"],
    spec["location"],
    COUNTRY,
    "Full-time",
    spec.get("work_mode", ""),
    posting,
    apply_url,
    today,
    "",
    f"{CURRENCY} {spec.get('salary', DEFAULT_SAL)} target",
    exp,
    techs,
    score,
    "none (Tier 3 empty)",
    str(folder / RES_NAME),
    str(folder / CL_NAME),
    status,
    "",
    "",
    "No",
    (now + dt.timedelta(days=7)).strftime("%Y-%m-%d"),
    today,
    f"{today} {AGENT}: {notes}",
]
upsert_application(DEFAULT_TRACKER_PATH, row)
st_p = H / "sweep_state.json"
if st_p.exists():
    st = json.loads(st_p.read_text(encoding="utf-8"))
    st.get("claims", {}).pop(spec["company"], None)
    st["next_app_id_hint"] = f"APP-{max(nums) + 2:03d}"
    st["last_heartbeat_at"] = now.isoformat(timespec="seconds")
    st["last_active_agent"] = AGENT
    st_p.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print(app, spec["company"], status)
