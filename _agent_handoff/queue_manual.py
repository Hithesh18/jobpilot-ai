r"""Push a ready package to Manual_Apply_Queue.xlsx + note in tracker + drop from sweep_state ready queue.
Usage: python _agent_handoff/queue_manual.py <spec.json>   (spec = update_manual_queue entry; app_id required)"""
import datetime as dt
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from update_manual_queue import upsert_manual_queue  # noqa: E402
from update_tracker_batch import DEFAULT_TRACKER_PATH, upsert_application  # noqa: E402

spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
upsert_manual_queue(spec)
now = dt.datetime.now().astimezone()
today = now.strftime("%Y-%m-%d")
ws = load_workbook(DEFAULT_TRACKER_PATH)["Applications"]
for r in ws.iter_rows(min_row=2):
    if r[0].value == spec["app_id"]:
        row = [c.value if c.value is not None else "" for c in r[:25]]
        row += [""] * (25 - len(row))
        row[23] = today
        row[24] = (str(row[24]) + " | " if row[24] else "") + f"{today}: MANUAL QUEUE - {spec.get('blocker_detail','')}"
        upsert_application(DEFAULT_TRACKER_PATH, row)
        break
sp = H / "sweep_state.json"
st = json.loads(sp.read_text(encoding="utf-8-sig"))
st["ready_to_submit_immediately"] = [x for x in st.get("ready_to_submit_immediately", []) if x.get("app_id") != spec["app_id"]]
st["last_heartbeat_at"] = now.isoformat(timespec="seconds")
sp.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print("queued", spec["app_id"], "ready left", len(st["ready_to_submit_immediately"]))
