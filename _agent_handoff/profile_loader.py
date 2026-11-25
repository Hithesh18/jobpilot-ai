"""
Centralized Candidate Profile & Workspace Path Resolver (`_agent_handoff/profile_loader.py`).
Shared across all Python scripts so zero personal data or machine-specific paths are hardcoded.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

HANDOFF_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = HANDOFF_DIR.parent
PROFILE_PATH = WORKSPACE_ROOT / "candidate_profile.json"

DEFAULT_PROFILE = {
    "candidate": {
        "first_name": "Alex",
        "last_name": "Morgan",
        "full_name": "Alex Morgan",
        "salutation_en": "Mr.",
        "salutation_de": "Herr",
        "gender": "Male",
        "date_of_birth_iso": "2000-06-15",
        "date_of_birth_de": "15.06.2000",
        "date_of_birth_us": "06/15/2000",
        "nationality": "Canadian",
        "email": "alex.morgan.dev@example.com",
        "phone": "+49 170 0000000",
        "address": {
            "street": "Torstrasse",
            "street_number": "120",
            "additional": "Apt 4B",
            "postal_code": "10119",
            "city": "Berlin",
            "region": "Berlin",
            "country": "Germany",
            "country_de": "Deutschland",
            "display_location": "Berlin, Germany",
        },
        "links": {
            "linkedin_url": "https://linkedin.com/in/alex-morgan-example",
            "linkedin_display": "linkedin.com/in/alex-morgan-example",
            "github_url": "https://github.com/alex-morgan-example",
            "github_display": "github.com/alex-morgan-example",
            "portfolio_url": "https://alex-morgan-dev.example.com",
            "portfolio_display": "alex-morgan-dev.example.com",
            "flagship_project_url": "https://kiezhub.example.org",
            "flagship_project_display": "kiezhub.example.org",
        },
        "education": {
            "current_degree": "M.Sc. in Computer Science",
            "current_university": "Technical University of Berlin",
            "graduation_month_year": "November 2026",
        },
        "availability": {
            "earliest_start_iso": "2026-12-01",
            "earliest_start_de": "01.12.2026",
            "earliest_start_us": "12/01/2026",
            "earliest_start_prose": "1 December 2026",
            "notice_period_number": "2",
            "notice_period_unit_en": "Weeks",
            "notice_period_unit_de": "Wochen",
        },
        "work_authorization": {
            "authorized_in_target_country": True,
            "requires_visa_sponsorship": False,
            "permit_type": "Time-limited work permit / Befristete Arbeitserlaubnis (eligible for full-time EU Blue Card transition)",
            "open_to_relocation": True,
        },
        "compensation": {
            "currency": "EUR",
            "default_range": "EUR 60,000 - 70,000",
            "default_number": "65000",
            "junior_mid_number": "60000",
            "mid_regular_number": "65000",
            "include_in_cover_letter_by_default": False,
        },
        "spoken_languages": {
            "resume_spoken_line": "English (fluent), German (A2, actively improving)",
            "english_level": "C1 / Fluent",
            "german_level": "A2 / Elementary",
            "max_allowed_german_requirement": "A2",
        },
        "files": {
            "resume_pdf_name": "Alex_Morgan_Resume.pdf",
            "cover_letter_pdf_name": "Alex_Morgan_Cover_Letter.pdf",
            "transcript_pdf_relpath": "_agent_handoff/Transcript.pdf",
        },
    },
    "targeting": {
        "profession": "Software Engineering",
        "target_country": "Germany",
        "primary_city": "Berlin",
        "target_locations": [
            ["Germany", "101282230"],
            ["Berlin, Germany", ""],
            ["Munich, Bavaria, Germany", ""],
            ["Hamburg, Germany", ""],
            ["Frankfurt, Hesse, Germany", ""],
            ["Cologne, North Rhine-Westphalia, Germany", ""],
        ],
        "yoe_min": 0,
        "yoe_max": 4,
        "hard_block_yoe_min": 5,
        "min_honest_fit_score": 82,
        "permanent_do_not_apply": [
            "northstar cloud",
            "pulseevent",
            "coretel systems",
        ],
    },
    "employers": {
        "current": {
            "name": "Northstar Cloud GmbH",
            "header_tex": "Northstar Cloud GmbH, Berlin",
            "city": "Berlin",
            "ai_feature_name": "AtlasCopilot",
        },
        "previous_1": {
            "name": "PulseEvent Technologies",
            "header_tex": "PulseEvent Technologies, Berlin",
            "city": "Berlin",
        },
        "previous_2": {
            "name": "CoreTel Systems",
            "header_tex": "CoreTel Systems, Toronto",
            "city": "Toronto",
        },
    },
    "experience_anchors": {
        "s1": "Build and release SaaS features end to end with TypeScript, Node.js, Express.js, Vue.js 3, PostgreSQL, and MongoDB.",
        "s4": "Closed a tenant-isolation gap in subscription APIs by enforcing strict JWT/OAuth 2.0 and RBAC checks, backed by regression tests.",
        "m1": "Built event-registration and ticketing features end to end with React, TypeScript, NestJS REST APIs, BullMQ background jobs, and MongoDB data models.",
        "t1": "Developed customer-facing enterprise billing and reporting interfaces using React, Angular, JavaScript, and SQL.",
        "t2": "Owned the Account Reconciliation module end to end and built reusable React and backend components that improved response times.",
        "th": "an interactive 3D scene viewer (React 19, TypeScript, react-three-fiber) where WebSocket state synchronization drives per-client camera framing across four urban models.",
        "p1": "Open-source neighborhood booking portal (equipment sharing, rooms, workshops): React 18, TypeScript, Vite, Node.js, Express, and MongoDB Atlas, with JWT moderation and OTP email verification.",
    },
    "forbidden_resume_terms": [
        "spring boot",
        "c#",
        "asp.net",
        "dotnet",
        "golang",
        "rust",
        "apache kafka",
        "ruby on rails",
        "symfony",
        "laravel",
        "blazor",
        "alexalex",
    ],
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            user_data = json.loads(PROFILE_PATH.read_text(encoding="utf-8-sig"))
            return _deep_merge(DEFAULT_PROFILE, user_data)
        except Exception:
            pass
    return DEFAULT_PROFILE


def get_python_exe() -> str:
    return os.environ.get("PYTHON_EXE") or sys.executable


def get_tectonic_exe() -> str:
    env_tect = os.environ.get("TECTONIC_EXE")
    if env_tect and Path(env_tect).exists():
        return env_tect
    bin_name = "tectonic.exe" if os.name == "nt" else "tectonic"
    local_bin = HANDOFF_DIR / "bin" / bin_name
    if local_bin.exists():
        return str(local_bin)
    found = shutil.which("tectonic")
    if found:
        return found
    return str(local_bin)


def resume_pdf_filename(profile: dict | None = None) -> str:
    p = profile or load_profile()
    files = p.get("candidate", {}).get("files", {})
    if files.get("resume_pdf_name"):
        return files["resume_pdf_name"]
    full = re.sub(r"[^A-Za-z0-9]+", "_", p["candidate"]["full_name"]).strip("_")
    return f"{full}_Resume.pdf"


def cover_letter_pdf_filename(profile: dict | None = None) -> str:
    p = profile or load_profile()
    files = p.get("candidate", {}).get("files", {})
    if files.get("cover_letter_pdf_name"):
        return files["cover_letter_pdf_name"]
    full = re.sub(r"[^A-Za-z0-9]+", "_", p["candidate"]["full_name"]).strip("_")
    return f"{full}_Cover_Letter.pdf"
