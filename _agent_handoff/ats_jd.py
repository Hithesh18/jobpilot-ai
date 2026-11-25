"""Fetch full job description JSON/text directly from Ashby, Greenhouse, and Lever public APIs."""
import html
import re
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0"}


def clean(t):
    t = re.sub(r"<br\s*/?>|</li>|</p>|</h\d>", "\n", t or "")
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def get(u):
    m = re.search(r"jobs\.ashbyhq\.com/([^/]+)/([0-9a-f-]{36})", u)
    if m:
        d = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{m[1]}?includeCompensation=true", headers=H, timeout=20).json()
        for j in d.get("jobs", []):
            if j["id"] == m[2]:
                return dict(
                    title=j["title"],
                    loc=j.get("location"),
                    sec=[s.get("location") for s in j.get("secondaryLocations", [])],
                    remote=j.get("isRemote"),
                    posted=j.get("publishedAt"),
                    company=m[1],
                    text=j.get("descriptionPlain") or clean(j.get("descriptionHtml")),
                )
        return dict(err="ashby job not found (closed?)")
    m = re.search(r"greenhouse\.io/([^/]+)/jobs/(\d+)", u)
    if m:
        j = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{m[1]}/jobs/{m[2]}", headers=H, timeout=20).json()
        return dict(
            title=j.get("title"),
            loc=(j.get("location") or {}).get("name"),
            posted=j.get("updated_at"),
            company=m[1],
            text=clean(html.unescape(j.get("content", ""))),
        )
    m = re.search(r"lever\.co/([^/]+)/([0-9a-f-]{36})", u)
    if m:
        j = requests.get(f"https://api.lever.co/v0/postings/{m[1]}/{m[2]}", headers=H, timeout=20).json()
        if "text" not in j:
            return dict(err=str(j)[:200])
        txt = (
            j.get("descriptionPlain", "")
            + "\n"
            + "\n".join(l["text"] + ":\n" + clean(l["content"]) for l in j.get("lists", []))
            + "\n"
            + (j.get("additionalPlain") or "")
        )
        return dict(
            title=j["text"],
            loc=j["categories"].get("location"),
            all=j["categories"].get("allLocations"),
            wt=j.get("workplaceType"),
            posted=j.get("createdAt"),
            company=m[1],
            text=txt,
        )
    return dict(err="unsupported")


if __name__ == "__main__":
    n = int(re.sub(r"\D", "", "0" + (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("-") else ""))) or 2500
    for u in [a for a in sys.argv[1:] if not a.startswith("-")]:
        try:
            d = get(u)
        except Exception as e:
            d = dict(err=str(e)[:200])
        t = d.pop("text", "") or ""
        print("=====", u[:110])
        print({k: v for k, v in d.items()})
        g = re.findall(r"(?i)[^\n.]{0,60}(?:german|deutsch)[^\n.]{0,60}|[^\n.]{0,40}\d\+? ?(?:-\d+ )?years[^\n.]{0,50}", t)[:6]
        print("  LANG/EXP:", g)
        print(t[:n])
