r"""
Shared Excel Tracker Upsert Utility (`_agent_handoff/update_tracker_batch.py`)
Usage from Python:
    from update_tracker_batch import upsert_application, DEFAULT_TRACKER_PATH
    upsert_application(DEFAULT_TRACKER_PATH, row_25_cols)

25-Column Schema for `Applications` sheet in `Application_Tracker.xlsx`:
  1. Application ID          (e.g., "APP-001" — always check `sync_status.py` first)
  2. Company Name            (e.g., "Example GmbH")
  3. Job Title               (exact title from JD)
  4. Job Location            (e.g., "Berlin" / "Munich" / "Germany (Remote)")
  5. Country                 ("Germany")
  6. Job Type                ("Full-time")
  7. Employment Type         ("Remote" / "Hybrid" / "On-site")
  8. Job Posting URL         (LinkedIn / StepStone / portal discovery URL)
  9. Company Careers URL     (Direct ATS URL or Easy Apply URL)
 10. Application Date        ("YYYY-MM-DD" date SUBMITTED)
 11. Application Deadline    (deadline if stated, else "")
 12. Salary Range            (JD salary or target range)
 13. Required Experience     (e.g., "Junior-Mid (1-4 yrs)")
 14. Key Technologies        (comma-separated verified skills matched)
 15. ATS Match Score         (integer out of 100, e.g., 92)
 16. Critical Missing Skills (unverified JD keywords honestly omitted from CV)
 17. Resume Version          ("<Folder>/<Candidate>_Resume.pdf")
 18. Cover Letter Version    ("<Folder>/<Candidate>_Cover_Letter.pdf")
 19. Application Status      ("Applied" / "Not Applied" / "Rejected" / ...)
 20. Recruiter Name          (recruiter name if shown, else "")
 21. Recruiter Email         (careers/recruiter email if shown, else "")
 22. Interview Date          ("No" or scheduled date/stage)
 23. Follow-up Date          ("YYYY-MM-DD", +7 days after Application Date)
 24. Last Updated            ("YYYY-MM-DD")
 25. Additional Notes        (Recency "<24h" or "48-64h", portal type, confirmation text)
"""
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, Side

DEFAULT_TRACKER_PATH = str(Path(__file__).resolve().parent.parent / "Application_Tracker.xlsx")


def upsert_application(filepath: str, row_data: list) -> int:
    wb = load_workbook(filepath)
    ws = wb["Applications"] if "Applications" in wb.sheetnames else wb.active

    app_id = row_data[0]
    target_row = None

    for r in range(2, ws.max_row + 1):
        val = ws.cell(row=r, column=1).value
        if val == app_id:
            target_row = r
            break
        if val is None or str(val).strip() == "":
            target_row = r
            break

    if target_row is None:
        target_row = ws.max_row + 1

    thin_side = Side(border_style="thin", color="D9D9D9")
    data_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    default_font = Font(name="Calibri", size=10)
    link_font = Font(name="Calibri", size=10, color="0563C1", underline="single")
    center_cols = {1, 5, 6, 7, 10, 11, 15, 19, 22, 23, 24}

    ws.row_dimensions[target_row].height = 36

    for col_idx, value in enumerate(row_data, start=1):
        cell = ws.cell(row=target_row, column=col_idx)
        cell.value = value if value != "" else None
        cell.border = data_border
        if col_idx in {8, 9} and value:
            cell.hyperlink = value
            cell.font = link_font
        else:
            cell.font = default_font
        cell.alignment = Alignment(
            horizontal="center" if col_idx in center_cols else "left",
            vertical="center",
            wrap_text=(col_idx in {13, 14, 16, 17, 18, 25}),
        )

    wb.save(filepath)
    print(f"Successfully updated row {target_row} ({app_id}) in {filepath}")
    return target_row
