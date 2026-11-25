r"""
Mark an existing tracker row as Applied + remove it from sweep_state.json ready queue + heartbeat.
Usage: python _agent_handoff/mark_applied.py <APP-ID> "<note appended to Notes>" [agent]
"""
import datetime as dt
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from update_tracker_batch import DEFAULT_TRACKER_PATH, upsert_application  # noqa: E402

app, note = sys.argv[1], sys.argv[2]
agent = sys.argv[3] if len(sys.argv) > 3 else "Claude"
now = dt.datetime.now().astimezone()
today = now.strftime("%Y-%m-%d")

ws = load_workbook(DEFAULT_TRACKER_PATH)["Applications"]
row = None
for r in ws.iter_rows(min_row=2):
    if r[0].value == app:
        row = [c.value if c.value is not None else "" for c in r[:25]]
        break
if row is None:
    raise SystemExit(f"{app} not found in tracker")
row += [""] * (25 - len(row))
row[9] = today
row[18] = "Applied"
row[22] = (now + dt.timedelta(days=7)).strftime("%Y-%m-%d")
row[23] = today
row[24] = (str(row[24]) + " | " if row[24] else "") + f"{today} {agent}: {note}"
upsert_application(DEFAULT_TRACKER_PATH, row)

sp = H / "sweep_state.json"
st = json.loads(sp.read_text(encoding="utf-8"))
st["ready_to_submit_immediately"] = [x for x in st.get("ready_to_submit_immediately", []) if x.get("app_id") != app]
st["last_active_agent"] = agent
st["last_heartbeat_at"] = now.isoformat(timespec="seconds")
sp.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{app} -> Applied; ready queue now {len(st['ready_to_submit_immediately'])}")
