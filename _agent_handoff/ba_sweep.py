r"""
Deep Arbeitsagentur (BA) sweep — also covers Make it in Germany (which lists BA jobs by the same reference number).
Usage: python _agent_handoff/ba_sweep.py <days|since> [--max-pages N]
  - Searches Germany-wide + candidate primary city region (from `candidate_profile.json`)
  - Paginates up to `--max-pages` (default 10)
  - Drops RED_TITLE + duplicate companies, fetches full JD, and keeps postings passing language/YOE/stack gates.
Writes `_ba_sweep_<days>d.json` and prints GREEN rows.
"""
import base64
import json
import random
import re
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from ats_poll import HARD_YOE_WORDS, RED_TITLE, german_requirement, is_dup_company, load_known_company_keys  # noqa: E402
from li_sweep import GER_LINE, GOOD_STACK, RED_STACK, YOE  # noqa: E402
from profile_loader import load_profile  # noqa: E402

PROF = load_profile()
PRIMARY_CITY = PROF.get("targeting", {}).get("primary_city", "Berlin")

HDR = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Mozilla/5.0"}
QS = [
    "Full Stack Developer",
    "Fullstack Developer",
    "Full Stack Engineer",
    "Frontend Developer",
    "Frontend Engineer",
    "Backend Developer",
    "Software Engineer",
    "Software Developer",
    "Web Developer",
    "React",
    "Vue.js",
    "TypeScript",
    "Node.js",
    "Next.js",
    "JavaScript",
    "AI Engineer",
    "Junior Software",
    "Junior Developer",
    "Three.js",
    "LLM",
]
WHERE = [None, (PRIMARY_CITY, 50)]
GER_WORDS = re.compile(r"\b(und|wir|die|der|für|mit|Sie|du|Erfahrung|Kenntnisse|bieten|Aufgaben)\b")


def search(days, max_pages):
    jobs = {}
    for q in QS:
        for where in WHERE:
            for page in range(1, max_pages + 1):
                p = {"was": q, "veroeffentlichtseit": days, "size": 100, "page": page, "angebotsart": 1}
                if where:
                    p.update(wo=where[0], umkreis=where[1])
                try:
                    r = requests.get(
                        "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs",
                        params=p,
                        headers=HDR,
                        timeout=30,
                    )
                except Exception:
                    time.sleep(3)
                    continue
                if r.status_code != 200:
                    break
                lst = r.json().get("ergebnisliste", [])
                for j in lst:
                    loc = (j.get("stellenlokationen") or [{}])[0].get("adresse", {}).get("ort", "")
                    jobs.setdefault(
                        j["referenznummer"],
                        dict(
                            ref=j["referenznummer"],
                            title=j.get("stellenangebotsTitel") or "",
                            company=j.get("firma") or "",
                            loc=loc,
                            posted=j.get("datumErsteVeroeffentlichung"),
                            ext=j.get("externeURL") or j.get("externeUrl", ""),
                            q=q,
                            region=where[0] if where else "DE",
                        ),
                    )
                if len(lst) < 100:
                    break
                time.sleep(random.uniform(1.5, 3))
    return jobs


def detail(ref):
    try:
        r = requests.get(
            "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/"
            + base64.b64encode(ref.encode()).decode(),
            headers=HDR,
            timeout=25,
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def main():
    days = sys.argv[1] if len(sys.argv) > 1 else "14"
    mp = int(sys.argv[sys.argv.index("--max-pages") + 1]) if "--max-pages" in sys.argv else 10
    from seen_cache import SeenCache

    sc = SeenCache("arbeitsagentur_ba")
    if days == "since":
        days = "1"
    keys = load_known_company_keys()
    jobs = search(days, mp)
    st = dict(cards=len(jobs), cached=0, red_title=0, dup=0, german_jd=0, red_jd=0, green=0)
    green = []
    for j in jobs.values():
        if sc.seen(j["ref"]) and "--rescreen" not in sys.argv:
            st["cached"] += 1
            continue
        if RED_TITLE.search(j["title"]):
            st["red_title"] += 1
            sc.mark(j["ref"], "red_title")
            continue
        if is_dup_company(j["company"], keys):
            st["dup"] += 1
            sc.mark(j["ref"], "dup")
            continue
        d = detail(j["ref"])
        jd = d.get("stellenangebotsBeschreibung", "") or ""
        words = len(jd.split()) or 1
        german_written = len(GER_WORDS.findall(jd)) / words > 0.03
        if german_written:
            st["german_jd"] += 1
        j["german_written"] = german_written
        reasons = []
        gr = german_requirement(jd)
        if gr:
            reasons.append("German required: " + gr[:80])
        rs = set(x.lower() for x in RED_STACK.findall(jd))
        gs = set(x.lower() for x in GOOD_STACK.findall(jd))
        if rs and len(gs) < 2:
            reasons.append("red stack " + ",".join(sorted(rs)))
        if not gs:
            reasons.append("no TS/JS/AI stack")
        hi = [int(y.group(1)) for y in YOE.finditer(jd) if int(y.group(1)) <= 15]
        if HARD_YOE_WORDS.search(jd):
            reasons.append("YOE>=5 (words)")
        if hi and min(hi) >= 5:
            reasons.append(f"YOE>={min(hi)}")
        j.update(
            url="https://www.arbeitsagentur.de/jobsuche/jobdetail/" + j["ref"],
            mig="https://www.make-it-in-germany.com/en/working-in-germany/job-listings/job/job-" + j["ref"],
            stack=sorted(gs),
            red_stack=sorted(rs),
            yoe=[y.group(0).strip() for y in YOE.finditer(jd)][:3],
            german=[g.group(0).strip() for g in GER_LINE.finditer(jd)][:3],
            reasons=reasons,
            jd=jd[:6000],
        )
        if reasons:
            st["red_jd"] += 1
            sc.mark(j["ref"], "red", "; ".join(reasons))
        else:
            st["green"] += 1
            green.append(j)
            sc.mark(j["ref"], "green", j["company"] + " | " + j["title"])
        time.sleep(random.uniform(1.5, 3))
    sc.finish()
    (H / f"_ba_sweep_{days}d.json").write_text(json.dumps(dict(stats=st, green=green), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(st))
    for j in green:
        print(
            f"GREEN | {j['company']} | {j['title']} | {j['loc']} | {j['posted']} | {j['url']} | ext={j['ext']}\n"
            f"   stack={j['stack']} red={j['red_stack']}\n   yoe={j['yoe']}\n   german={j['german']}"
        )


if __name__ == "__main__":
    main()
