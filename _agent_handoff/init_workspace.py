#!/usr/bin/env python3
"""
First-Time Workspace Bootstrap & Reset Utility (`_agent_handoff/init_workspace.py`).

Creates (if missing, or overwrites when `--reset` is passed):
  1. `Application_Tracker.xlsx` — styled 25-column `Applications` sheet + live formula-driven `Dashboard` sheet (0 personal rows)
  2. `Manual_Apply_Queue.xlsx` — styled 18-column `Manual_Queue` sheet including `Copy_Paste_Pitch_Max_3_Sentences` & `Copy_Paste_All_Form_Answers` (0 personal rows)
  3. `_agent_handoff/sweep_state.json` — clean synchronized cursor state (`next_app_id_hint: "APP-001"`)
  4. `_private_account_logins.txt` — copied from `_private_account_logins.example.txt` if missing (gitignored)
  5. `_agent_handoff/bin/tectonic[.exe]` — auto-downloads the official `tectonic-typesetting/tectonic` release binary for Windows / macOS / Linux if `tectonic` is not already installed!

Usage:
  python _agent_handoff/init_workspace.py [--reset] [--skip-tectonic]
"""
import argparse
import io
import json
import os
import platform
import shutil
import stat
import tarfile
import urllib.request
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

HANDOFF_DIR = Path(__file__).resolve().parent
ROOT = HANDOFF_DIR.parent

TRACKER_HEADERS_AND_WIDTHS = [
    ("Application ID", 16),
    ("Company Name", 24),
    ("Job Title", 30),
    ("Job Location", 20),
    ("Country", 15),
    ("Job Type", 18),
    ("Employment Type", 18),
    ("Job Posting URL", 28),
    ("Company Careers URL", 28),
    ("Application Date", 16),
    ("Application Deadline", 18),
    ("Salary Range", 18),
    ("Required Experience", 20),
    ("Key Technologies", 38),
    ("ATS Match Score", 16),
    ("Critical Missing Skills", 30),
    ("Resume Version", 22),
    ("Cover Letter Version", 22),
    ("Application Status", 20),
    ("Recruiter Name", 20),
    ("Recruiter Email", 26),
    ("Interview Date", 16),
    ("Follow-up Date", 16),
    ("Last Updated", 16),
    ("Additional Notes", 40),
]

PORTAL_KEYS = [
    "ats_multi_platform_apis",
    "google_ats_dorks",
    "join_com",
    "stepstone_de",
    "linkedin_de",
    "indeed_de",
    "xing_jobs",
    "wearedevelopers",
    "englishjobs_de",
    "arbeitsagentur_ba",
    "make_it_in_germany",
    "get_in_it",
    "jobvector",
    "yourfirm_jobware_stellenanzeigen_jobmesh",
    "monster_joblift_talent_jobsde_glassdoor",
]


def build_application_tracker(xlsx_path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Applications"

    navy_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin = Side(border_style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.row_dimensions[1].height = 28
    for idx, (title, width) in enumerate(TRACKER_HEADERS_AND_WIDTHS, start=1):
        c = ws.cell(row=1, column=idx, value=title)
        c.fill = navy_fill
        c.font = hdr_font
        c.border = border
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        col_letter = openpyxl.utils.get_column_letter(idx)
        ws.column_dimensions[col_letter].width = width
    ws.freeze_panes = "A2"

    # Build live formula-backed Dashboard sheet
    dash = wb.create_sheet(title="Dashboard")
    title_font = Font(name="Calibri", size=15, bold=True, color="1F4E78")
    sec_font = Font(name="Calibri", size=12, bold=True, color="1F4E78")
    kpi_hdr_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    kpi_hdr_font = Font(name="Calibri", size=10, bold=True, color="1F4E78")
    kpi_val_font = Font(name="Calibri", size=13, bold=True, color="000000")

    dash.cell(row=2, column=2, value="Job Application Summary Dashboard").font = title_font

    kpis = [
        ("Total Applications", "=COUNTA(Applications!A2:A2000)", "0"),
        (
            "Active Pipeline",
            '=COUNTIFS(Applications!S2:S2000,"<>Not Applied",Applications!S2:S2000,"<>Rejected",Applications!S2:S2000,"<>Withdrawn",Applications!S2:S2000,"<>")',
            "0",
        ),
        (
            "Interview Stage",
            '=COUNTIF(Applications!S2:S2000,"HR Screening")+COUNTIF(Applications!S2:S2000,"Technical Interview")+COUNTIF(Applications!S2:S2000,"Final Interview")+COUNTIF(Applications!S2:S2000,"Offer")',
            "0",
        ),
        (
            "Interview Conversion Rate",
            '=IF(COUNTA(Applications!A2:A2000)=0,0,(COUNTIF(Applications!S2:S2000,"HR Screening")+COUNTIF(Applications!S2:S2000,"Technical Interview")+COUNTIF(Applications!S2:S2000,"Final Interview")+COUNTIF(Applications!S2:S2000,"Offer"))/COUNTA(Applications!A2:A2000))',
            "0.0%",
        ),
        ("Offers Received", '=COUNTIF(Applications!S2:S2000,"Offer")', "0"),
        ("Average Fit Score", "=IFERROR(AVERAGE(Applications!O2:O2000),0)", "0.0"),
    ]
    for offset, (label, formula, num_fmt) in enumerate(kpis):
        col = 2 + offset
        hc = dash.cell(row=4, column=col, value=label)
        hc.fill = kpi_hdr_fill
        hc.font = kpi_hdr_font
        hc.border = border
        hc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        vc = dash.cell(row=5, column=col, value=formula)
        vc.font = kpi_val_font
        vc.border = border
        vc.number_format = num_fmt
        vc.alignment = Alignment(horizontal="center", vertical="center")
        dash.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 24

    dash.cell(row=7, column=2, value="Applications by Status").font = sec_font
    for col, txt in ((2, "Status"), (3, "Count"), (4, "% Share")):
        c = dash.cell(row=8, column=col, value=txt)
        c.fill = navy_fill
        c.font = hdr_font
        c.alignment = Alignment(horizontal="center", vertical="center")

    statuses = [
        "Not Applied",
        "Applied",
        "Assessment",
        "HR Screening",
        "Technical Interview",
        "Final Interview",
        "Offer",
        "Rejected",
        "Withdrawn",
    ]
    for idx, st in enumerate(statuses, start=9):
        c1 = dash.cell(row=idx, column=2, value=st)
        c2 = dash.cell(row=idx, column=3, value=f'=COUNTIF(Applications!$S$2:$S$2000, "{st}")')
        c3 = dash.cell(row=idx, column=4, value=f"=IF($B$5=0, 0, C{idx}/$B$5)")
        c3.number_format = "0.0%"
        for c in (c1, c2, c3):
            c.border = border

    wb.save(xlsx_path)
    print(f"[Init] Created clean {xlsx_path} (25 styled columns + Dashboard, 0 rows)")


def build_manual_queue(xlsx_path: Path) -> None:
    import sys

    sys.path.insert(0, str(HANDOFF_DIR))
    from update_manual_queue import HEADERS, _style_headers

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Manual_Queue"
    ws.append(HEADERS)
    _style_headers(ws)
    wb.save(xlsx_path)
    print(f"[Init] Created clean {xlsx_path} (18 styled columns, 0 rows)")


def build_sweep_state(state_path: Path) -> None:
    now = datetime.now().astimezone()
    start_14d = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    state = {
        "schema_version": "2.0",
        "phase": "BACKLOG_14D_PLUS_24H_FIRST",
        "backlog_window_start": start_14d,
        "backlog_14d_all_complete": False,
        "realtime_interval_minutes": 30,
        "last_active_agent": "None (Fresh Workspace)",
        "last_heartbeat_at": now.isoformat(timespec="seconds"),
        "last_realtime_sweep_at": None,
        "next_app_id_hint": "APP-001",
        "ready_to_submit_immediately": [],
        "claims": {},
        "pending_tracker_logs": [],
        "portal_last_sweep": {},
        "portals": {
            p: {
                "last_24h_sweep_at": None,
                "backlog_14d_completed": False,
                "verified_14d_screened_count": 0,
                "backlog_14d_cursor": "page=1",
            }
            for p in PORTAL_KEYS
        },
        "session_log": [
            {
                "at": now.isoformat(timespec="seconds"),
                "agent": "init_workspace.py",
                "note": "Initialized clean synchronized dual-agent workspace.",
            }
        ],
    }
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Init] Created clean {state_path} (next_app_id_hint=APP-001)")


def ensure_private_logins_file() -> None:
    target = ROOT / "_private_account_logins.txt"
    example = ROOT / "_private_account_logins.example.txt"
    if not target.exists() and example.exists():
        shutil.copy2(example, target)
        print(f"[Init] Created local gitignored {target} from example template")


def ensure_tectonic_binary() -> None:
    bin_dir = HANDOFF_DIR / "bin"
    bin_name = "tectonic.exe" if os.name == "nt" else "tectonic"
    local_bin = bin_dir / bin_name
    if local_bin.exists():
        print(f"[Init] Tectonic binary already present at {local_bin}")
        return
    sys_tect = shutil.which("tectonic")
    if sys_tect:
        print(f"[Init] Tectonic found on system PATH: {sys_tect}")
        return

    print("[Init] Querying latest official tectonic-typesetting/tectonic release from GitHub...")
    sys_os = platform.system().lower()
    machine = platform.machine().lower()
    if sys_os == "windows":
        asset_sub = "x86_64-pc-windows-msvc.zip"
    elif sys_os == "darwin":
        asset_sub = "aarch64-apple-darwin.tar.gz" if ("arm" in machine or "aarch64" in machine) else "x86_64-apple-darwin.tar.gz"
    else:
        asset_sub = "aarch64-unknown-linux-gnu.tar.gz" if ("arm" in machine or "aarch64" in machine) else "x86_64-unknown-linux-gnu.tar.gz"

    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        rel = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
        dl_url = None
        for a in rel.get("assets", []):
            name = a.get("name", "")
            if asset_sub in name:
                dl_url = a.get("browser_download_url")
                break
        if not dl_url:
            print(f"[Init] WARN: Could not find matching Tectonic asset ({asset_sub}) in latest release. Install tectonic manually or set TECTONIC_EXE.")
            return

        bin_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Init] Downloading {dl_url} ...")
        raw_bytes = urllib.request.urlopen(urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()
        if dl_url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                for member in zf.namelist():
                    if member.endswith("tectonic.exe"):
                        local_bin.write_bytes(zf.read(member))
                        break
        else:
            with tarfile.open(fileobj=io.BytesIO(raw_bytes), mode="r:gz") as tf:
                for member in tf.getmembers():
                    if member.name.endswith("tectonic") and member.isfile():
                        f_obj = tf.extractfile(member)
                        if f_obj:
                            local_bin.write_bytes(f_obj.read())
                            local_bin.chmod(local_bin.stat().st_mode | stat.S_IEXEC)
                        break
        if local_bin.exists():
            print(f"[Init] Installed Tectonic binary -> {local_bin}")
    except Exception as e:
        print(f"[Init] WARN: Auto-download of Tectonic skipped/failed ({e}). Install tectonic via cargo/brew/choco or place binary in {bin_dir}.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Initialize clean trackers, state, and LaTeX compiler for the Dual-Agent Job Engine.")
    ap.add_argument("--reset", action="store_true", help="Overwrite existing tracker Excel files and sweep_state.json with empty templates.")
    ap.add_argument("--skip-tectonic", action="store_true", help="Skip checking/downloading the portable Tectonic LaTeX binary.")
    args = ap.parse_args()

    tracker = ROOT / "Application_Tracker.xlsx"
    manual_q = ROOT / "Manual_Apply_Queue.xlsx"
    sweep_st = HANDOFF_DIR / "sweep_state.json"

    if args.reset or not tracker.exists():
        build_application_tracker(tracker)
    else:
        print(f"[Init] Keeping existing {tracker} (pass --reset to wipe)")

    if args.reset or not manual_q.exists():
        build_manual_queue(manual_q)
    else:
        print(f"[Init] Keeping existing {manual_q} (pass --reset to wipe)")

    if args.reset or not sweep_st.exists():
        build_sweep_state(sweep_st)
    else:
        print(f"[Init] Keeping existing {sweep_st} (pass --reset to wipe)")

    ensure_private_logins_file()

    if not args.skip_tectonic:
        ensure_tectonic_binary()

    print("[Init] Workspace ready! Run `python _agent_handoff/sync_status.py` to verify.")


if __name__ == "__main__":
    main()
