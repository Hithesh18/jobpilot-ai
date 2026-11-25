r"""
LinkedIn guest-API sweep with full JD screening (shared by Claude Code + Gemini Antigravity).
Usage:
  python _agent_handoff/li_sweep.py <hours|since> [--pages N] [--out file.json]
    hours: 24 (Phase 1), 336 (14-day backlog), or `since` (incremental since last sweep)
Searches target locations configured in `candidate_profile.json` with 0-4 YOE queries, drops RED_TITLE / dup companies,
fetches every remaining JD via LinkedIn's public guest API, and prints GREEN candidates.
"""
import html
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from ats_poll import HARD_YOE_WORDS, RED_TITLE, german_requirement, is_dup_company, load_known_company_keys  # noqa: E402
from profile_loader import load_profile  # noqa: E402
from seen_cache import SeenCache  # noqa: E402


def nap(lo, hi):
    time.sleep(random.uniform(lo, hi))


PROF = load_profile()
TARG = PROF.get("targeting", {})

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
QUERIES = [
    "Junior Full Stack Developer",
    "Full Stack Developer",
    "Full Stack Engineer",
    "Junior Frontend Developer",
    "Frontend Developer",
    "Frontend Engineer",
    "React Developer",
    "Next.js Developer",
    "Vue.js Developer",
    "TypeScript Developer",
    "Node.js Developer",
    "Backend Developer Node.js",
    "Junior Software Engineer",
    "Software Engineer TypeScript",
    "Web Developer",
    "Junior AI Engineer",
    "AI Engineer",
    "Mid-Level Software Engineer",
    "Graduate Software Engineer",
    "Three.js Developer",
]
DEFAULT_LOCATIONS = [
    ("Germany", "101282230"),
    ("Berlin, Germany", ""),
    ("Munich, Bavaria, Germany", ""),
    ("Hamburg, Germany", ""),
    ("Frankfurt, Hesse, Germany", ""),
    ("Cologne, North Rhine-Westphalia, Germany", ""),
]
cfg_locs = TARG.get("target_locations")
LOCATIONS = [tuple(x) for x in cfg_locs] if isinstance(cfg_locs, list) and cfg_locs else DEFAULT_LOCATIONS
if "--cities-only" in sys.argv and len(LOCATIONS) > 2:
    LOCATIONS = LOCATIONS[2:]

HOME_EXTRA = ["Software Engineer", "Software Developer", "Developer", "Engineer TypeScript"]
RED_STACK = re.compile(
    r"\b(java|spring boot|kotlin|\.net|c#|golang|php|laravel|symfony|ruby on rails|scala|abap|salesforce|"
    r"c\+\+|embedded|flutter|swift|react native)\b",
    re.I,
)
GOOD_STACK = re.compile(
    r"\b(typescript|javascript|react|next\.js|nextjs|vue|nuxt|node\.?js|nestjs|express|three\.js|webgl|"
    r"langchain|langgraph|llm|rag)\b",
    re.I,
)
YOE = re.compile(r"[^.\n]{0,60}\b(\d{1,2})\s*(?:\+|-|–|to)?\s*(\d{1,2})?\+?\s*(?:years|yrs|jahre)[^.\n]{0,60}", re.I)
GER_LINE = re.compile(r"[^.\n]{0,90}\b(german|deutsch)[^.\n]{0,90}", re.I)

_CONSEC_429 = 0


def get(u, tries=2):
    global _CONSEC_429
    for i in range(tries):
        try:
            res = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=20).read().decode("utf-8", "ignore")
            _CONSEC_429 = 0
            return res
        except urllib.error.HTTPError as e:
            if e.code == 429:
                _CONSEC_429 += 1
                if _CONSEC_429 >= 3:
                    return "__LI_429__"
                time.sleep(25 * (i + 1))
                continue
            return ""
        except Exception:
            time.sleep(2)
    return ""


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()


def search(hours, pages, sc=None, locs=None):
    tpr = f"r{hours * 3600}"
    jobs = {}
    use_locs = locs if locs is not None else LOCATIONS
    home_loc = use_locs[1][0] if len(use_locs) > 1 else use_locs[0][0]
    plan = [(q, loc, geo) for loc, geo in use_locs for q in QUERIES] + [(q, home_loc, "") for q in HOME_EXTRA]
    for q, loc, geo in plan:
        for st in range(0, 25 * pages, 25):
            u = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords="
                + urllib.parse.quote(q)
                + "&location="
                + urllib.parse.quote(loc)
                + (f"&geoId={geo}" if geo else "")
                + f"&f_TPR={tpr}&sortBy=DD&start={st}"
            )
            h = get(u)
            n = 0
            fresh = 0
            if h == "__LI_429__":
                print("LI guest API 429 rate-limit active; stopping search politely to let IP cool down.", flush=True)
                return jobs
            for m in re.finditer(
                r'data-entity-urn="urn:li:jobPosting:(\d+)".*?<h3 class="base-search-card__title">\s*(.*?)\s*</h3>'
                r'.*?<h4 class="base-search-card__subtitle">(.*?)</h4>.*?<span class="job-search-card__location">\s*(.*?)\s*</span>'
                r'(?:.*?<time[^>]*datetime="([^"]+)")?',
                h,
                re.S,
            ):
                n += 1
                jid = m.group(1)
                fresh += 0 if (sc and sc.seen(jid)) else 1
                jobs.setdefault(
                    jid,
                    dict(
                        id=jid,
                        title=clean(m.group(2)),
                        company=clean(m.group(3)),
                        loc=clean(m.group(4)),
                        posted=m.group(5) or "",
                        q=q,
                    ),
                )
            if n < 10 or (sc and fresh == 0):
                nap(2.2, 4.0)
                break
            nap(4, 7)
    return jobs


def main():
    sc = SeenCache("linkedin")
    incremental = len(sys.argv) > 1 and sys.argv[1] == "since"
    hours = sc.hours_since_last(24) if incremental else (int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 24)
    pages = int(sys.argv[sys.argv.index("--pages") + 1]) if "--pages" in sys.argv else (2 if hours <= 24 else 6)
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else H / f"_li_sweep_{'since' if incremental else hours}h.json"
    use_locs = LOCATIONS[:2] if (incremental and "--all-cities" not in sys.argv and "--cities-only" not in sys.argv) else LOCATIONS
    print(f"window={hours}h incremental={incremental} locs={len(use_locs)} cached_ids={len(sc.d)}", flush=True)
    keys = load_known_company_keys()
    jobs = search(hours, pages, None if "--rescreen" in sys.argv else sc, locs=use_locs)
    stats = dict(cards=len(jobs), cached=0, red_title=0, dup=0, red_jd=0, green=0)
    green = []
    for j in jobs.values():
        if sc.seen(j["id"]) and "--rescreen" not in sys.argv:
            stats["cached"] += 1
            continue
        if RED_TITLE.search(j["title"]):
            stats["red_title"] += 1
            sc.mark(j["id"], "red_title")
            if (stats["red_title"] + stats["dup"]) % 25 == 0:
                sc.save()
            continue
        if is_dup_company(j["company"], keys):
            stats["dup"] += 1
            sc.mark(j["id"], "dup")
            if (stats["red_title"] + stats["dup"]) % 25 == 0:
                sc.save()
            continue
        page = get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{j['id']}")
        if page == "__LI_429__":
            print("LI guest API 429 during JD fetch; saving progress and stopping politely.", flush=True)
            break
        if not page:
            continue
        m = re.search(r'<div class="show-more-less-html__markup[^"]*">(.*?)</div>', page, re.S)
        jd = clean(m.group(1)) if m else ""
        j["jd_len"] = len(jd)
        reasons = []
        if not jd:
            reasons.append("no-JD")
        gr = german_requirement(jd)
        if gr:
            reasons.append("German required: " + gr[:80])
        j["german_written"] = len(re.findall(r"\b(und|wir|die|der|für|mit|Sie|du|Erfahrung|Kenntnisse)\b", jd)) > 15
        rs = set(x.lower() for x in RED_STACK.findall(jd))
        gs = set(x.lower() for x in GOOD_STACK.findall(jd))
        if rs and len(gs) < 2:
            reasons.append("red stack: " + ",".join(sorted(rs)))
        if not gs:
            reasons.append("no TS/JS/AI stack")
        yoe = [y.group(0).strip() for y in YOE.finditer(jd)][:3]
        hi = [int(y.group(1)) for y in YOE.finditer(jd) if int(y.group(1)) <= 15]
        if HARD_YOE_WORDS.search(jd):
            reasons.append("YOE>=5 (words)")
        if hi and min(hi) >= 5:
            reasons.append(f"YOE>=5 ({min(hi)})")
        j.update(
            yoe=yoe,
            german=[g.group(0).strip() for g in GER_LINE.finditer(jd)][:3],
            stack=sorted(gs),
            red_stack=sorted(rs),
            url=f"https://www.linkedin.com/jobs/view/{j['id']}/",
            reasons=reasons,
            jd=jd,
        )
        if reasons:
            stats["red_jd"] += 1
            sc.mark(j["id"], "red", "; ".join(reasons))
        else:
            stats["green"] += 1
            green.append(j)
            sc.mark(j["id"], "green", j["company"] + " | " + j["title"])
        if (stats["red_jd"] + stats["green"]) % 20 == 0:
            sc.save()
        nap(3, 5)
    sc.finish()
    out.write_text(json.dumps(dict(stats=stats, green=green, all=list(jobs.values())), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats))
    for j in green:
        print(
            f"GREEN | {j['company']} | {j['title']} | {j['loc']} | {j['posted']} | {j['url']}\n"
            f"   stack={j['stack']} red={j['red_stack']}\n   yoe={j['yoe']}\n   german={j['german']}"
        )


if __name__ == "__main__":
    main()
