#!/usr/bin/env python3
r"""
Cross-Agent Synchronization Audit Script (Shared by Claude Code & Gemini Antigravity)
Synchronizes:
  1. `Application_Tracker.xlsx` (main 25-column tracker + Dashboard)
  2. `Manual_Apply_Queue.xlsx` (dedicated sheet of CAPTCHA/blocked jobs;
     if user changes `Manual_Status` to `Applied`, auto-syncs into `Application_Tracker.xlsx`!)
  3. `_agent_handoff/sweep_state.json` (shared timestamp + portal cursor brain)

Run FIRST every session (and whenever user says `run`):
  python _agent_handoff/sync_status.py
"""
import json
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HANDOFF = Path(__file__).resolve().parent
ROOT = HANDOFF.parent
sys.path.insert(0, str(HANDOFF))
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
TRACKER = ROOT / "Application_Tracker.xlsx"
MANUAL_QUEUE = ROOT / "Manual_Apply_Queue.xlsx"
SWEEP_STATE = HANDOFF / "sweep_state.json"

_dna = set(x.lower().strip() for x in PROF.get("targeting", {}).get("permanent_do_not_apply", []) if x)
for emp in PROF.get("employers", {}).values():
    if isinstance(emp, dict) and emp.get("name"):
        _dna.add(emp["name"].lower().strip())
PERMANENT_DO_NOT_APPLY = _dna


def norm_company(name: str) -> str:
    s = (name or "").lower().strip()
    s = re.sub(r"\b(gmbh|ag|se|ug|kg|inc|ltd|corp|holding|technologies|technology|software|germany|deutschland)\b", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def sync_manual_queue_back_to_tracker():
    """If the user manually applied to a row in Manual_Apply_Queue.xlsx and marked it Applied, update main tracker."""
    if not MANUAL_QUEUE.exists() or not TRACKER.exists():
        return 0, []
    import openpyxl

    mwb = openpyxl.load_workbook(MANUAL_QUEUE, data_only=True)
    mws = mwb["Manual_Queue"] if "Manual_Queue" in mwb.sheetnames else mwb.active

    pending_manual = []
    manually_applied_ids = []
    for r in mws.iter_rows(min_row=2, values_only=True):
        if not r or not any(r):
            continue
        aid = str(r[0] or "").strip()
        comp = str(r[1] or "").strip()
        role = str(r[2] or "").strip()
        blocker = str(r[8] or "").strip()
        mstatus = str(r[14] or "").strip()
        if mstatus.lower().startswith("applied") and aid:
            manually_applied_ids.append(aid)
        elif not mstatus.lower().startswith("skip"):
            pending_manual.append((aid, comp, role, blocker))

    synced_count = 0
    if manually_applied_ids:
        twb = openpyxl.load_workbook(TRACKER)
        tws = twb["Applications"] if "Applications" in twb.sheetnames else twb.active
        today = datetime.now().strftime("%Y-%m-%d")
        for r_idx in range(2, tws.max_row + 1):
            tid = str(tws.cell(row=r_idx, column=1).value or "").strip()
            tstat = str(tws.cell(row=r_idx, column=19).value or "").strip()
            if tid in manually_applied_ids and tstat.lower() != "applied":
                tws.cell(row=r_idx, column=19, value="Applied")
                tws.cell(row=r_idx, column=24, value=today)
                synced_count += 1
        if synced_count > 0:
            twb.save(TRACKER)

    return synced_count, pending_manual


def load_rows(xlsx_path: Path):
    import openpyxl

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Applications"] if "Applications" in wb.sheetnames else wb.active
    return [[str(v or "") for v in r] for r in ws.iter_rows(values_only=True)]


def main() -> None:
    if not TRACKER.exists():
        print(f"ERROR: Tracker not found at {TRACKER}. Run `python _agent_handoff/init_workspace.py` first.")
        return

    synced_manual, pending_manual = sync_manual_queue_back_to_tracker()

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        shutil.copy2(TRACKER, tmp_path)
        all_rows = load_rows(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    headers = [str(c or "").strip() for c in all_rows[0]]

    def col_idx(candidates):
        for cand in candidates:
            for idx, h in enumerate(headers):
                if cand.lower() in h.lower():
                    return idx
        return -1

    id_col = col_idx(["app id", "id"])
    comp_col = col_idx(["company"])
    role_col = col_idx(["job title", "role", "position"])
    status_col = col_idx(["application status", "status"])

    total_rows = 0
    max_id_num = 0
    status_counts = {}
    applied_companies = set()
    all_tracked_companies = set()
    pending_rows = []

    for row in all_rows[1:]:
        if not any(str(x).strip() for x in row):
            continue
        total_rows += 1
        app_id = str(row[id_col]).strip() if 0 <= id_col < len(row) else ""
        m = re.search(r"(\d+)", app_id)
        if m:
            max_id_num = max(max_id_num, int(m.group(1)))
        comp = str(row[comp_col]).strip() if 0 <= comp_col < len(row) else ""
        role = str(row[role_col]).strip() if 0 <= role_col < len(row) else ""
        status = str(row[status_col] or "Unknown").strip() if 0 <= status_col < len(row) else "Unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

        if comp:
            all_tracked_companies.add(comp)
            if status.lower() == "applied":
                applied_companies.add(comp)

        s_low = status.lower()
        if s_low != "applied" and not any(k in s_low for k in ("rejected", "skipped", "disqualified", "closed", "blocked")):
            pending_rows.append((app_id, comp, role, status))

    print("=" * 76)
    print("CLAUDE <-> GEMINI 24/7 SYNCHRONIZED ENGINE STATUS")
    print("=" * 76)
    print(f"Workspace Root          : {ROOT}")
    print(f"Candidate Profile       : {PROF.get('candidate', {}).get('full_name')} ({PROF.get('targeting', {}).get('profession')})")
    print(f"Total Tracker Rows      : {total_rows}")
    print(f"Unique Companies Tracked: {len(all_tracked_companies)} (Applied: {len(applied_companies)})")
    print(f"Next Available App ID   : APP-{max_id_num + 1:03d}")
    print(f"Status Breakdown        : {status_counts}")
    print(f"Manual Queue Excel      : {MANUAL_QUEUE} ({len(pending_manual)} pending manual; {synced_manual} newly synced to Applied)")
    print(f"Permanent Do-Not-Apply  : {sorted(PERMANENT_DO_NOT_APPLY)}")

    if pending_rows:
        print("\n[1] Non-Applied / Pending Rows in Application_Tracker.xlsx:")
        for aid, c, r, st in pending_rows:
            print(f"    - {aid}: {c} | {r} [{st}]")

    if SWEEP_STATE.exists():
        st = json.loads(SWEEP_STATE.read_text(encoding="utf-8"))
        ready_q = st.get("ready_to_submit_immediately", [])
        portals = st.get("portals", {})
        unfinished_14d = [k for k, v in portals.items() if not v.get("backlog_14d_completed")]
        print("\n[2] Shared Timestamp & Cursor State (_agent_handoff/sweep_state.json):")
        print(f"    - Current Phase        : {st.get('phase')} (14d backlog complete: {st.get('backlog_14d_all_complete')})")
        print(f"    - Last Active Agent    : {st.get('last_active_agent')} @ {st.get('last_heartbeat_at')}")
        print(f"    - Ready-on-Disk Queue  : {len(ready_q)} packages -> {[x.get('company') for x in ready_q]}")
        print(f"    - 14d Portals Remaining: {len(unfinished_14d)} -> {unfinished_14d}")
    print("=" * 76)


if __name__ == "__main__":
    main()
