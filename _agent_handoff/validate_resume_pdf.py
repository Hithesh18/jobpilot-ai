#!/usr/bin/env python3
"""
Mandatory 1-Page Full-Coverage & Humanized Cover Letter QA Gate (Shared by Claude & Gemini)
Works with `pypdf` OR built-in `pdftotext`/`pdfinfo` (zero-dependency fallback).
Reads candidate links, spoken line, and forbidden terms dynamically from `candidate_profile.json`.

Usage:
  python _agent_handoff/validate_resume_pdf.py <path_to_Resume.pdf>
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_loader import cover_letter_pdf_filename, load_profile  # noqa: E402


def _build_rules():
    prof = load_profile()
    cand = prof.get("candidate", {})
    links_obj = cand.get("links", {})
    req_links = [
        links_obj.get("linkedin_display", ""),
        links_obj.get("github_display", ""),
        links_obj.get("portfolio_display", ""),
    ]
    req_links = [x for x in req_links if x]

    first = (cand.get("first_name") or "alex").split()[0].lower()
    dup_name = first + first
    forbidden = list(prof.get("forbidden_resume_terms", []))
    if dup_name and dup_name not in [x.lower() for x in forbidden]:
        forbidden.append(dup_name)

    spoken_line = cand.get("spoken_languages", {}).get(
        "resume_spoken_line", "English (fluent), German (A2, actively improving)"
    )
    cl_name = cover_letter_pdf_filename(prof)
    return req_links, forbidden, spoken_line, cl_name


def extract_pages_and_text(pdf_path: str):
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)
        txt = "\n".join((p.extract_text() or "") for p in reader.pages)
        return num_pages, txt
    except ImportError:
        if shutil.which("pdfinfo") and shutil.which("pdftotext"):
            info = subprocess.check_output(["pdfinfo", pdf_path], text=True, errors="replace")
            m = re.search(r"Pages:\s+(\d+)", info)
            num_pages = int(m.group(1)) if m else 0
            txt = subprocess.check_output(["pdftotext", pdf_path, "-"], text=True, errors="replace")
            return num_pages, txt
        raise RuntimeError("Install `pypdf` (`pip install pypdf`) or `poppler-utils` (`pdftotext`/`pdfinfo`).")


def validate_cover_letter_pdf(cl_pdf: Path, forbidden_terms: list[str]) -> None:
    cl_pages, cl_raw = extract_pages_and_text(str(cl_pdf))
    assert cl_pages == 1, f"FAIL: Cover Letter must be strictly 1 page, got {cl_pages} pages in {cl_pdf}"
    cl_norm = re.sub(r"\s+", " ", cl_raw.replace("\ufb01", "fi").replace("\ufb02", "fl")).strip()
    assert "__" not in cl_norm, f"FAIL: Unreplaced template placeholder found in {cl_pdf}"
    cl_body = cl_norm.split("Subject:", 1)[-1] if "Subject:" in cl_norm else cl_norm
    m_dash = re.search(r"—|–|\s-\s|•", cl_body)
    assert not m_dash, (
        f"FAIL: Cover Letter contains forbidden dash/bullet '{m_dash.group(0)}' "
        f"(must be 100% plain human paragraphs, no '-', '–', '—', or bullets) in {cl_pdf}"
    )
    m_cl_ai = re.search(
        r"\b(?:tailored|tailor|customi[sz]ed|bespoke|seamlessly|seamless|uncompromising|rock-solid|relentlessly|"
        r"delighted|thrilled|passionate|excited|leverage|leveraging|synergy|cutting-edge|uniquely positioned|"
        r"testament to|honed my skills)\b|at the intersection of|thrive in|aligns directly|i am writing to express",
        cl_body,
        re.I,
    )
    assert not m_cl_ai, f"FAIL: Cover Letter contains AI-sounding phrase '{m_cl_ai.group(0)}' in {cl_pdf}"
    for bad in forbidden_terms:
        assert re.sub(r"\s+", "", bad.lower()) not in re.sub(r"\s+", "", cl_norm.lower()), (
            f"FAIL: Forbidden/unverified claim '{bad}' found in Cover Letter {cl_pdf}"
        )


def validate_pdf(pdf_path: str) -> None:
    req_links, forbidden_terms, spoken_line, cl_name = _build_rules()
    num_pages, raw_txt = extract_pages_and_text(pdf_path)
    assert num_pages == 1, f"FAIL: Expected strictly 1 page, got {num_pages} pages in {pdf_path}"

    txt = raw_txt.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\ufb00", "ff")
    norm_txt = re.sub(r"\s+", " ", txt).strip()
    compact_txt = re.sub(r"\s+", "", txt)
    low_compact = compact_txt.lower()

    # 1. Check required 3 header links
    for link in req_links:
        assert re.sub(r"\s+", "", link.lower()) in low_compact, (
            f"FAIL: Missing official header link '{link}' in {pdf_path}"
        )

    # 2. Check zero duplicate section/skill labels (especially Spoken:)
    for label in [
        "Spoken:",
        "Languages:",
        "Web and Frameworks:",
        "Data and Messaging:",
        "Cloud and DevOps:",
        "AI Engineering:",
        "Testing and Tools:",
    ]:
        c_lbl = re.sub(r"\s+", "", label)
        cnt = compact_txt.count(c_lbl)
        assert cnt == 1, f"FAIL: Skill label '{label}' appeared {cnt} times (must be strictly 1) in {pdf_path}"

    # 3. Check exact clean Spoken line (no commute/city junk inside Spoken)
    expected_spoken_compact = re.sub(r"\s+", "", f"Spoken:{spoken_line}")
    assert expected_spoken_compact in compact_txt, (
        f"FAIL: Spoken line must be exact 'Spoken: {spoken_line}' in {pdf_path}"
    )

    # 4. Check Summary length: strictly clean 4-5 full lines (400 to 650 chars)
    m_sum = re.search(r"Summary\s*(.*?)\s*Skills\s*(?:Languages|[A-Za-z ]+):", norm_txt, re.S)
    assert m_sum, f"FAIL: Could not parse Summary -> Skills block in {pdf_path}"
    summary_txt = m_sum.group(1).strip()
    assert 400 <= len(summary_txt) <= 650, (
        f"FAIL: Summary must be a clean 4-5 full lines (400-650 chars), got {len(summary_txt)} chars in {pdf_path}"
    )

    # 5. Check zero forbidden / forged skills
    for bad in forbidden_terms:
        assert re.sub(r"\s+", "", bad.lower()) not in low_compact, (
            f"FAIL: Forbidden/unverified skill or broken slug '{bad}' found in {pdf_path}"
        )

    # 6. Check FULL 1-PAGE coverage (>= 3550 chars ensures 95-98% vertical A4 page fill with zero bottom gap)
    clean_len = len(norm_txt)
    assert clean_len >= 3550, (
        f"FAIL: Resume text too sparse ({clean_len} chars < 3550 minimum) — leaves wasted empty space at bottom of page!"
    )

    # 7. Also validate sibling Cover Letter PDF if present
    p_obj = Path(pdf_path)
    cl_candidates = [p_obj.parent / cl_name]
    if p_obj.name == "SAMPLE_GOLDEN_RESUME.pdf":
        cl_candidates.append(p_obj.parent / "SAMPLE_GOLDEN_COVER_LETTER.pdf")
    for cl_pdf in cl_candidates:
        if cl_pdf.exists():
            validate_cover_letter_pdf(cl_pdf, forbidden_terms)

    print(
        f"PASS QA: {pdf_path} (Strictly 1 full page, {clean_len} chars, Summary={len(summary_txt)} chars, 0 duplicates, 0 forged skills, CL humanized)"
    )


if __name__ == "__main__":
    validate_pdf(sys.argv[1])
