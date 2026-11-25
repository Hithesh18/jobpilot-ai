#!/usr/bin/env python3
r"""
Shared Manual-Application Queue Helper for Claude Code & Gemini Antigravity (`Manual_Apply_Queue.xlsx`).

Whenever ANY Green Zone job has a 100% tailored & QA-passing CV + Cover Letter on disk,
but cannot be submitted automatically due to:
  - Visual CAPTCHA / Cloudflare Turnstile / hCaptcha / reCAPTCHA / anti-bot block
  - Pre-existing account needing user password reset (never reset existing passwords!)
  - Extra personal document scan required (e.g., residence/work-permit scan)
  - Unconfirmed legal/security-clearance/background-check declaration

Both Claude and Gemini MUST call `upsert_manual_queue(...)` (in addition to logging in
`Application_Tracker.xlsx`) AND MUST populate `copy_paste_pitch` (a plain, 100% human-written
<=3-sentence answer to "What makes you a strong fit / Why us / Message to hiring team") AND
`copy_paste_answers` (exact copy-paste answers to every form question on that page) so the user
can copy-paste and submit in 20 seconds.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

HANDOFF = Path(__file__).resolve().parent
ROOT = HANDOFF.parent
sys.path.insert(0, str(HANDOFF))
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
CAND = PROF.get("candidate", {})
EMPS = PROF.get("employers", {})
DEFAULT_MANUAL_XLSX = ROOT / "Manual_Apply_Queue.xlsx"

HEADERS = [
    "App_ID",
    "Company",
    "Role_Title",
    "Location",
    "Work_Mode",
    "Portal_ATS",
    "Direct_Apply_URL",
    "Job_Listing_URL",
    "Blocker_Category",
    "Why_Agent_Could_Not_Submit",
    "German_Requirement_Line",
    "Tailored_Resume_PDF",
    "Tailored_Cover_Letter_PDF",
    "Quick_Manual_Steps",
    "Manual_Status",
    "Added_At",
    "Copy_Paste_Pitch_Max_3_Sentences",
    "Copy_Paste_All_Form_Answers",
]

COL_WIDTHS = [12, 26, 40, 20, 12, 24, 48, 42, 24, 46, 38, 56, 56, 54, 22, 22, 72, 68]

FORBIDDEN_AI_TOKENS = re.compile(
    r"\b(tailored|tailor|customi[sz]ed|bespoke|delve|testament|underscore|seamlessly|aligns directly|standout match|pleased to apply|thrilled|moreover|furthermore|spearheaded)\b|—",
    re.I,
)


def default_form_answers(salary: str | None = None) -> str:
    comp_cfg = CAND.get("compensation", {})
    sal_str = salary or f"{comp_cfg.get('currency', 'EUR')} {comp_cfg.get('default_number', '65000')} gross/year"
    addr = CAND.get("address", {})
    auth = CAND.get("work_authorization", {})
    avail = CAND.get("availability", {})
    return (
        f"Full Name: {CAND.get('full_name', 'Alex Morgan')}\n"
        f"First Name: {CAND.get('first_name', 'Alex')} | Last Name: {CAND.get('last_name', 'Morgan')}\n"
        f"Email: {CAND.get('email', 'alex.morgan.dev@example.com')} | Phone: {CAND.get('phone', '+49 170 0000000')}\n"
        f"Salary Expectation: {sal_str}\n"
        f"Earliest Start Date: {avail.get('earliest_start_de', '01.12.2026')}\n"
        f"Authorized to work: {'Yes (no visa sponsorship required)' if auth.get('authorized_in_target_country', True) else 'Requires sponsorship'}\n"
        f"Work Permit Type: {auth.get('permit_type', 'Time-limited work permit')}\n"
        f"Nationality: {CAND.get('nationality', 'Canadian')} | Location: {addr.get('display_location', 'Berlin, Germany')} (open to relocate)"
    )


def default_pitch() -> str:
    cur_emp = EMPS.get("current", {}).get("name", "Northstar Cloud GmbH")
    prev1 = EMPS.get("previous_1", {}).get("name", "PulseEvent Technologies")
    prev2 = EMPS.get("previous_2", {}).get("name", "CoreTel Systems")
    cur_city = EMPS.get("current", {}).get("city", "Berlin")
    edu = CAND.get("education", {})
    avail = CAND.get("availability", {})
    return (
        f"Over 4+ years at {cur_emp}, {prev1}, and {prev2}, I have built and shipped production web and backend "
        f"systems end to end using TypeScript, Node.js, React, Vue 3, SQL, MongoDB, and Docker/Kubernetes CI/CD. "
        f"In my current role at {cur_emp} in {cur_city}, I own full-stack features, API integrations, and performance "
        f"optimizations from design through automated Playwright/Vitest testing and release. "
        f"I am finishing my {edu.get('current_degree', 'M.Sc. in Computer Science')} at {edu.get('current_university', 'Technical University of Berlin')}, "
        f"hold a valid work permit, and am available full-time starting {avail.get('earliest_start_de', '01.12.2026')}."
    )


def _style_headers(ws):
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    for col_idx, (hdr, width) in enumerate(zip(HEADERS, COL_WIDTHS), start=1):
        cell = ws.cell(row=1, column=col_idx, value=hdr)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        col_letter = openpyxl.utils.get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width
    ws.freeze_panes = "A2"


def _ensure_workbook(xlsx_path: Path):
    if xlsx_path.exists():
        wb = openpyxl.load_workbook(xlsx_path)
        ws = wb["Manual_Queue"] if "Manual_Queue" in wb.sheetnames else wb.active
        ws.title = "Manual_Queue"
        _style_headers(ws)
        return wb, ws

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Manual_Queue"
    ws.append(HEADERS)
    _style_headers(ws)
    return wb, ws


def upsert_manual_queue(entry: dict, xlsx_path: Path = DEFAULT_MANUAL_XLSX) -> int:
    wb, ws = _ensure_workbook(xlsx_path)

    app_id = str(entry.get("app_id", "")).strip()
    company = str(entry.get("company", "")).strip()
    role_title = str(entry.get("role_title", "")).strip()
    now_iso = entry.get("added_at") or datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

    pitch = str(entry.get("copy_paste_pitch", "")).strip() or default_pitch()
    bad = FORBIDDEN_AI_TOKENS.search(pitch)
    if bad:
        raise ValueError(
            f"Blocked AI/meta token '{bad.group(0)}' in copy_paste_pitch for {company}. "
            f"Write plain, human 2-3 sentences with zero em-dashes and never mention 'tailored'!"
        )

    form_qa = str(entry.get("copy_paste_answers", "")).strip() or default_form_answers()

    row_values = [
        app_id,
        company,
        role_title,
        str(entry.get("location", "")).strip(),
        str(entry.get("work_mode", "")).strip(),
        str(entry.get("portal_ats", "")).strip(),
        str(entry.get("direct_apply_url", "")).strip(),
        str(entry.get("job_listing_url", "")).strip(),
        str(entry.get("blocker_category", "CAPTCHA / Anti-Bot")).strip(),
        str(entry.get("blocker_detail", "")).strip(),
        str(entry.get("german_line", "")).strip(),
        str(entry.get("resume_pdf", "")).strip(),
        str(entry.get("cover_letter_pdf", "")).strip(),
        str(entry.get("quick_steps", "")).strip(),
        str(entry.get("manual_status", "Pending Manual Apply")).strip(),
        now_iso,
        pitch,
        form_qa,
    ]

    target_row = None
    for r_idx in range(2, ws.max_row + 1):
        existing_id = str(ws.cell(row=r_idx, column=1).value or "").strip()
        existing_comp = str(ws.cell(row=r_idx, column=2).value or "").strip().lower()
        if (app_id and existing_id == app_id) or (company and existing_comp == company.lower()):
            target_row = r_idx
            cur_status = str(ws.cell(row=r_idx, column=15).value or "").strip()
            if cur_status.lower().startswith("applied") and not entry.get("force_status"):
                row_values[14] = cur_status
            if not entry.get("added_at") and ws.cell(row=r_idx, column=16).value:
                row_values[15] = str(ws.cell(row=r_idx, column=16).value)
            break

    if target_row is None:
        target_row = ws.max_row + 1

    link_font = Font(color="0563C1", underline="single")
    pending_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    applied_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    for c_idx, val in enumerate(row_values, start=1):
        cell = ws.cell(row=target_row, column=c_idx, value=val)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if c_idx in (7, 8) and val.startswith(("http://", "https://", "mailto:")):
            cell.hyperlink = val
            cell.font = link_font
        if c_idx == 15:
            cell.fill = applied_fill if val.lower().startswith("applied") else pending_fill
            cell.font = Font(bold=True)

    wb.save(xlsx_path)
    print(f"[ManualQueue] Upserted row {target_row} ({app_id} - {company}) -> {xlsx_path}")
    return target_row


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python _agent_handoff/update_manual_queue.py <spec.json | json-array-file>")
        sys.exit(1)
    arg = sys.argv[1]
    p = Path(arg)
    payload = json.loads(p.read_text(encoding="utf-8")) if p.exists() else json.loads(arg)
    items = payload if isinstance(payload, list) else [payload]
    for item in items:
        upsert_manual_queue(item)
