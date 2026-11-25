r"""
Validated Sweep-State Updater (`_agent_handoff/state_upd.py`)
Usage:
  python _agent_handoff/state_upd.py <portal|-> <true|false|-> "<cursor|->" "<note|->" [--screened N] [--24h] [--24hall] [--agent Claude|Gemini]

ANTI-SHORTCUT GATE:
  Setting `completed=true` REQUIRES `--screened <N>` with `N >= 15` (real scraped/screened job postings)
  and REJECTS shortcut excuses ("aggregator", "cross-covered", "assumed via", "same feeds").
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

STATE_PATH = Path(__file__).resolve().parent / "sweep_state.json"
MIN_SCREENED_FOR_COMPLETE = 15
SHORTCUT_RE = re.compile(r"cross.?cover|assumed via|same .*feeds already swept|aggregator shortcut", re.I)

s = json.loads(STATE_PATH.read_text(encoding="utf-8"))
now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

pos_args = []
i = 1
screened_val = None
flag_24h = False
flag_24hall = False
agent_name = os.environ.get("AGENT_NAME", "Claude")
while i < len(sys.argv):
    a = sys.argv[i]
    if a == "--screened" and i + 1 < len(sys.argv):
        screened_val = int(sys.argv[i + 1])
        i += 2
    elif a == "--agent" and i + 1 < len(sys.argv):
        agent_name = sys.argv[i + 1]
        i += 2
    elif a == "--24h":
        flag_24h = True
        i += 1
    elif a == "--24hall":
        flag_24hall = True
        i += 1
    else:
        pos_args.append(a)
        i += 1

portal, comp, cur, note = (pos_args + ["-"] * 4)[:4]

if portal != "-":
    e = s["portals"].setdefault(portal, {})
    if screened_val is not None:
        e["verified_14d_screened_count"] = max(int(e.get("verified_14d_screened_count") or 0), screened_val)
    if comp == "true":
        eff_screened = int(e.get("verified_14d_screened_count") or 0)
        if eff_screened < MIN_SCREENED_FOR_COMPLETE:
            raise SystemExit(
                f"REJECTED shortcut completion for '{portal}': --screened {eff_screened} < {MIN_SCREENED_FOR_COMPLETE}. "
                f"Actually scrape & screen 14-day pages via CDP/API before marking complete!"
            )
        if SHORTCUT_RE.search(cur) or SHORTCUT_RE.search(note):
            raise SystemExit(f"REJECTED shortcut excuse in cursor/note for '{portal}'. Every portal must be directly scraped!")
        e["backlog_14d_completed"] = True
        e["backlog_14d_completed_at"] = now
    elif comp == "false":
        e["backlog_14d_completed"] = False
    if cur != "-":
        e["backlog_14d_cursor"] = cur
    if flag_24h:
        e["last_24h_sweep_at"] = now

if flag_24hall:
    for e in s["portals"].values():
        e["last_24h_sweep_at"] = now
    s["last_realtime_sweep_at"] = now

if note != "-":
    s.setdefault("session_log", []).append({"at": now, "agent": agent_name, "note": note})

s["last_active_agent"] = agent_name
s["last_heartbeat_at"] = now

all_done = bool(s["portals"]) and all(
    bool(e.get("backlog_14d_completed")) and int(e.get("verified_14d_screened_count") or 0) >= MIN_SCREENED_FOR_COMPLETE
    for e in s["portals"].values()
)
s["backlog_14d_all_complete"] = all_done
s["phase"] = "REALTIME_30M" if all_done else "BACKLOG_14D_PLUS_24H_FIRST"

STATE_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
open_portals = [
    k
    for k, e in s["portals"].items()
    if not (e.get("backlog_14d_completed") and int(e.get("verified_14d_screened_count") or 0) >= MIN_SCREENED_FOR_COMPLETE)
]
print("ok", now, s["phase"], f"open={len(open_portals)}", open_portals)
