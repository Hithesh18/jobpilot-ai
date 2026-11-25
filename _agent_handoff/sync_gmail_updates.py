"""
Automated Gmail Inbox Status Sync & Rejection Root-Cause Analyzer (`_agent_handoff/sync_gmail_updates.py`).
Scans recent Gmail inbox threads via the background Chrome CDP bridge (`s_gmail_scan_updates.js`),
classifies rejections vs. OA / interview invitations, updates `Application_Tracker.xlsx`, and writes a
structured postmortem summary to `_agent_handoff/last_gmail_sync_report.json`.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import openpyxl

HANDOFF = Path(__file__).resolve().parent
ROOT = HANDOFF.parent
sys.path.insert(0, str(HANDOFF))
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
FIRST_LOW = (PROF.get("candidate", {}).get("first_name") or "alex").split()[0].lower()
DUP_NAME_TOKEN = FIRST_LOW + FIRST_LOW

TRACKER_PATH = str(ROOT / "Application_Tracker.xlsx")
CDP_SCRIPT_PATH = str(HANDOFF / "cdp_scripts" / "s_gmail_scan_updates.js")
REPORT_PATH = str(HANDOFF / "last_gmail_sync_report.json")
RAW_ROWS_PATH = str(HANDOFF / "last_gmail_rows.json")

REJECTION_PATTERNS = [
    r"unfortunately",
    r"not to move forward",
    r"not be moving forward",
    r"not able to move forward",
    r"not be proceeding",
    r"other candidates",
    r"other qualified",
    r"isn't an ideal fit",
    r"not an ideal fit",
    r"don't see an ideal fit",
    r"do not see an ideal fit",
    r"i'm sorry that we",
    r"taken some time over the decision",
    r"truly inspired by the talented people",
    r"after careful consideration",
    r"after reviewing all applications",
    r"based on your profile and the number",
    r"does not fully match",
    r"closing this position",
    r"closed the position",
    r"unable to take your application",
    r"nicht optimal zu den anforderungen",
    r"leider nicht ber",
    r"regret to inform",
    r"unable to consider",
    r"unable to offer",
    r"cannot consider",
    r"won't be able to invite",
    r"won’t be able to invite",
    r"decided to move forward with",
    r"decided to continue with other",
    r"greatly appreciate it\.\s*however",
    r"nicht weiter ber",
    r"nicht mit in die engere wahl",
    r"nicht in die engere wahl",
    r"nach detaillierter pr",
    r"nach umfassender sichtung",
    r"leider",
    r"andere bewerber",
    r"anderen bewerbenden",
    r"den prozess mit anderen",
    r"absage",
]

SELECTION_PATTERNS = [
    r"next step",
    r"invite you to",
    r"would like to invite",
    r"like to move forward",
    r"schedule a call",
    r"schedule an interview",
    r"motivation snapshot",
    r"coding challenge",
    r"take-home",
    r"einladung zum",
    r"gerne kennenlernen",
]

IGNORE_SENDERS = [
    "linkedin job alerts",
    "xing jobs",
    "talent.com",
    "stepstone daily jobs",
    "indeed",
    "glassdoor",
    "jobleads",
    "hokify",
    "mailsuite",
    "google",
]

STOPWORDS = {
    "gmbh",
    "ag",
    "se",
    "inc",
    "ltd",
    "ug",
    "co",
    "kg",
    "europe",
    "germany",
    "technology",
    "technologies",
    "the",
    "and",
    "for",
    "via",
    "holding",
    "group",
    "solutions",
    "systems",
    "digital",
    "digitale",
    "software",
    "partner",
    "partners",
}


def fetch_gmail_rows():
    tmp_out = str(HANDOFF / "_gmail_direct_out.json")
    try:
        payload = json.dumps({"scriptPath": CDP_SCRIPT_PATH}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:9333",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if raw.get("ok"):
            rows = raw["result"]["rows"]
            Path(RAW_ROWS_PATH).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
            return rows
    except Exception:
        pass

    subprocess.run(
        ["node", str(HANDOFF / "cdp_scripts" / "run_direct.js"), CDP_SCRIPT_PATH, tmp_out],
        check=True,
        timeout=120,
    )
    raw = json.loads(Path(tmp_out).read_text(encoding="utf-8", errors="ignore"))
    rows = raw["result"]["rows"]
    Path(RAW_ROWS_PATH).write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return rows


def classify_email(row):
    sender = (row.get("senderName") or "").lower()
    subj = (row.get("subject") or "").lower()
    snip = (row.get("snippet") or "").lower()
    combined = f"{sender} | {subj} | {snip}"

    if any(ig in sender for ig in IGNORE_SENDERS):
        return None
    if sender == "linkedin" and "is hiring" in subj:
        return None
    if "your application" in subj and "has been sent" in subj and "stepstone" in sender:
        return None
    if "automatic reply" in subj or "automatische antwort" in subj:
        return None
    if "wir freuen uns" in snip and "bitte haben sie verst" in snip:
        return None
    if "has not been opened yet" in snip and "mailsuite" in sender:
        return None
    is_receipt_subj = bool(
        re.search(
            r"eingangsbestätigung|danke für deine bewerbung|vielen dank für ihre bewerbung|ist angekommen|"
            r"confirmation of your application|thank you for your application|wir haben ihre bewerbung.*erhalten|"
            r"application received|your application has been received",
            subj,
            re.I,
        )
    )
    is_hypothetical_no_reply = bool(re.search(r"sollten wir uns innerhalb der nächsten.*nicht.*gemeldet haben", snip, re.I))
    if is_receipt_subj and (
        is_hypothetical_no_reply
        or not re.search(r"\b(leider|unfortunately|absage|not be moving forward|other candidates|andere bewerber)\b", snip, re.I)
    ):
        return None

    for pat in REJECTION_PATTERNS:
        if re.search(pat, combined, re.I):
            return "Rejected"
    if "once again, we'd like to thank you for applying" in snip:
        return "Rejected"
    for pat in SELECTION_PATTERNS:
        if re.search(pat, combined, re.I):
            return "Selected"
    return None


def match_company(em, tracker_rows):
    header_hay = f"{em.get('senderName','')} {em.get('subject','')}".lower()
    full_hay = f"{header_hay} {em.get('snippet','')}".lower()

    for hay in (header_hay, full_hay):
        for tr in tracker_rows:
            comp_low = tr["company"].lower()
            base_comp = re.sub(r"\(.*?\)", "", comp_low).strip()
            tokens = [t for t in re.split(r"[^a-z0-9äöüß]+", base_comp) if len(t) >= 3 and t not in STOPWORDS]
            if not tokens:
                continue
            if len(tokens) == 1:
                if re.search(rf"\b{re.escape(tokens[0])}\b", hay):
                    return tr
            else:
                if (re.search(rf"\b{re.escape(tokens[0])}\b", hay) and re.search(rf"\b{re.escape(tokens[1])}\b", hay)) or (
                    len(tokens[0]) >= 6
                    and tokens[0] not in ("next", "control", "buying", "prior", "vision")
                    and re.search(rf"\b{re.escape(tokens[0])}\b", header_hay)
                ):
                    return tr
    return None


def analyze_cv_and_jd(folder_path, role_title, _company_name):
    reasons = []
    fine_tune = []
    jd_path = os.path.join(folder_path, "Job_Description.txt") if folder_path else ""
    tex_path = os.path.join(folder_path, "resume.tex") if folder_path else ""
    jd_text = Path(jd_path).read_text(encoding="utf-8", errors="ignore") if (jd_path and os.path.exists(jd_path)) else ""
    tex_text = Path(tex_path).read_text(encoding="utf-8", errors="ignore") if (tex_path and os.path.exists(tex_path)) else ""

    rt_low = role_title.lower()
    if any(k in rt_low for k in ["senior", "lead", "principal", "staff", "founding", "forward deployed"]):
        reasons.append(
            f"Seniority/Title Stretch: Role title '{role_title}' targets Senior/Lead/Founding (5+ YOE full-time), whereas EU HR discounts Working Student tenure."
        )
        fine_tune.append("Stick strictly to 0-4 YOE Junior/Mid-Level/regular Engineer roles (skipping bare Senior/Lead/Founding).")

    if any(k in rt_low for k in ["consulting", "consultant", "berater", "solution engineer"]):
        reasons.append(f"Client-Facing / Consulting Role ('{role_title}'): Typically requires C1/C2 local-language client communication.")
        fine_tune.append("Keep Consulting / Solutions Engineer roles on the Red-Zone skip list.")

    if "test" in rt_low or "qa" in rt_low or "sdet" in rt_low:
        reasons.append(
            f"Specialized QA/SDET Role ('{role_title}'): Competes against dedicated QA/SDET automation specialists rather than product developers."
        )
        fine_tune.append("Avoid dedicated QA/SDET-only roles; target product engineering roles where Playwright/Vitest/Jest is a core strength.")

    if tex_text and DUP_NAME_TOKEN in tex_text.lower():
        reasons.append(f"Duplicate autofill token detected ('{DUP_NAME_TOKEN}').")

    if jd_text:
        stack_gaps = []
        for label, pat in [
            ("Go / Golang", r"\b(golang|go)\b"),
            ("Rust", r"\brust\b"),
            ("C# / .NET", r"\b(c#|\.net)\b"),
            ("Ruby", r"\bruby\b"),
            ("Terraform", r"\bterraform\b"),
        ]:
            if re.search(pat, jd_text, re.I):
                stack_gaps.append(label)
        if stack_gaps:
            reasons.append(f"Core Stack Gap in JD: JD required {', '.join(stack_gaps)}, outside verified production stack.")
            fine_tune.append(f"Skip roles where {', '.join(stack_gaps)} is the primary backend requirement.")

    if not reasons:
        reasons.append("High applicant volume or subtle domain/language preference.")
    return reasons, fine_tune


def main():
    rows = fetch_gmail_rows()
    wb = openpyxl.load_workbook(TRACKER_PATH)
    ws = wb["Applications"] if "Applications" in wb.sheetnames else wb.active
    today_str = datetime.now().strftime("%Y-%m-%d")

    tracker_rows = []
    for r in range(2, ws.max_row + 1):
        app_id = str(ws.cell(r, 1).value or "").strip()
        comp = str(ws.cell(r, 2).value or "").strip()
        role = str(ws.cell(r, 3).value or "").strip()
        status = str(ws.cell(r, 19).value or "").strip()
        res_ver = str(ws.cell(r, 17).value or "").strip()
        notes = str(ws.cell(r, 25).value or "").strip()
        if comp:
            tracker_rows.append(
                {
                    "excel_row": r,
                    "app_id": app_id,
                    "company": comp,
                    "role": role,
                    "status": status,
                    "res_ver": res_ver,
                    "notes": notes,
                }
            )

    newly_updated = []

    for em in rows:
        sender = em.get("senderName") or ""
        subj = em.get("subject") or ""
        snip = em.get("snippet") or ""
        time_str = em.get("time") or ""

        kind = classify_email(em)
        if not kind:
            continue

        matched_tr = match_company(em, tracker_rows)
        if not matched_tr:
            continue

        r = matched_tr["excel_row"]
        cur_status = str(ws.cell(r, 19).value or "").strip()

        if kind == "Rejected" and cur_status != "Rejected":
            ws.cell(r, 19).value = "Rejected"
            ws.cell(r, 20).value = sender
            ws.cell(r, 23).value = "Closed"
            ws.cell(r, 24).value = today_str
            old_notes = str(ws.cell(r, 25).value or "")
            note_add = f" | Rejected {today_str} ({time_str}): Auto-synced from Gmail ({subj})."
            if f"Rejected {today_str}" not in old_notes:
                ws.cell(r, 25).value = (old_notes + note_add).strip(" |")

            folder_rel = matched_tr["res_ver"].split("/")[0].split("\\")[0] if matched_tr["res_ver"] else ""
            folder_abs = str(ROOT / folder_rel) if folder_rel else ""
            reasons, fine_tune = analyze_cv_and_jd(folder_abs, matched_tr["role"], matched_tr["company"])
            newly_updated.append(
                {
                    "app_id": matched_tr["app_id"],
                    "company": matched_tr["company"],
                    "role": matched_tr["role"],
                    "new_status": "Rejected",
                    "time": time_str,
                    "sender": sender,
                    "subject": subj,
                    "snippet": snip,
                    "folder": folder_abs,
                    "reasons": reasons,
                    "fine_tune": fine_tune,
                }
            )
            matched_tr["status"] = "Rejected"

        elif kind == "Selected" and cur_status == "Applied":
            ws.cell(r, 19).value = "HR Screening"
            ws.cell(r, 20).value = sender
            ws.cell(r, 24).value = today_str
            old_notes = str(ws.cell(r, 25).value or "")
            note_add = f" | Selected/Next Step {today_str} ({time_str}): {subj} - {snip[:140]}"
            ws.cell(r, 25).value = (old_notes + note_add).strip(" |")
            newly_updated.append(
                {
                    "app_id": matched_tr["app_id"],
                    "company": matched_tr["company"],
                    "role": matched_tr["role"],
                    "new_status": "HR Screening / Interview",
                    "time": time_str,
                    "sender": sender,
                    "subject": subj,
                    "snippet": snip,
                }
            )
            matched_tr["status"] = "HR Screening"

    wb.save(TRACKER_PATH)
    report = {
        "synced_at": datetime.now().isoformat(),
        "scanned_emails": len(rows),
        "newly_updated_count": len(newly_updated),
        "newly_updated": newly_updated,
    }
    Path(REPORT_PATH).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
