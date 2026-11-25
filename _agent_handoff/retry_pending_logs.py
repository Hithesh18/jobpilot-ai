r"""Retry tracker logs queued in sweep_state.json['pending_tracker_logs'] (e.g. when Application_Tracker.xlsx was open in Excel)."""
import json
import subprocess
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
P = H / "sweep_state.json"
if not P.exists():
    print("pending_tracker_logs: 0")
    sys.exit(0)
st = json.loads(P.read_text(encoding="utf-8"))
pend = st.get("pending_tracker_logs", [])
if not pend:
    print("pending_tracker_logs: 0")
    sys.exit(0)
left, done = [], []
for e in pend:
    r = subprocess.run([sys.executable, str(H / "log_applied.py"), *e["args"]], capture_output=True, text=True, encoding="utf-8")
    out = r.stdout + r.stderr
    if r.returncode != 0 or "PermissionError" in out:
        left.append(e)
    else:
        done.append(e["args"][0])
st = json.loads(P.read_text(encoding="utf-8"))
st["pending_tracker_logs"] = left
for f in done:
    for k in [k for k, v in st.get("claims", {}).items() if "tracker log pending" in str(v.get("note", ""))]:
        if k.split()[0].lower() in f.lower():
            st["claims"].pop(k, None)
P.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"pending_tracker_logs: logged {len(done)} {done}, still pending {len(left)}" + (" (Application_Tracker.xlsx locked)" if left else ""))
