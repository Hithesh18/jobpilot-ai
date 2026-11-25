"""Fetch full job description for one or more BA Jobsuche reference numbers."""
import base64
import re
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")
H = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Mozilla/5.0"}
GER = re.compile(r"\b(und|wir|die|der|für|mit|Sie|du|Erfahrung|Kenntnisse)\b")


def det(ref):
    r = requests.get(
        "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/" + base64.b64encode(ref.encode()).decode(),
        headers=H,
        timeout=20,
    )
    return r.json() if r.status_code == 200 else {}


if __name__ == "__main__":
    full = "--full" in sys.argv
    for ref in [a for a in sys.argv[1:] if not a.startswith("--")]:
        d = det(ref)
        t = d.get("stellenangebotsBeschreibung", "") or ""
        ger = len(GER.findall(t))
        words = len(t.split()) or 1
        lang = "DE" if ger / words > 0.04 else "EN"
        g = re.findall(r"(?i)[^\n.]{0,60}(?:german|deutsch)[^\n.]{0,60}|[^\n.]{0,40}\d\+? ?(?:-\d+ )?(?:years|jahre)[^\n.]{0,40}", t)[:5]
        print(
            "=====",
            ref,
            "|",
            d.get("firma"),
            "|",
            d.get("stellenangebotsTitel"),
            "|",
            lang,
            round(ger / words, 3),
            "| ext:",
            d.get("allianzpartnerUrl") or d.get("externeUrl", ""),
        )
        print("  ", g)
        if full or lang == "EN":
            print(t[: (6000 if full else 1200)])
