r"""
Public (NO-LOGIN) parallel multi-portal sweep — shared by Claude Code + Gemini Antigravity.
Uses guest HTTP access for fetching so logged-in sessions are reserved for applying.

One worker thread per portal runs in parallel; inside a portal requests are sequential with 2.5-5 s jitter, no cookies.
New job URLs (not in seen_cache) get their detail page fetched and screened with the shared rules
(RED_TITLE, dup company, german_requirement, RED_STACK, 5+ YOE). Output: _public_sweep.json + GREEN lines.

Usage:
  python _agent_handoff/public_portals.py [--max-detail N] [--only stepstone,xing]
"""
import concurrent.futures as cf
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
from seen_cache import SeenCache  # noqa: E402

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml",
}
Q = [
    "full-stack-developer",
    "frontend-developer",
    "junior-software-engineer",
    "react-developer",
    "vue-js-developer",
    "typescript-developer",
    "node-js-developer",
    "web-developer",
    "ai-engineer",
    "software-engineer",
]
QS = [q.replace("-", " ").replace("vue js", "Vue.js").replace("node js", "Node.js") for q in Q]
enc = urllib.parse.quote

PORTALS = {
    "stepstone": dict(
        base="https://www.stepstone.de/",
        search=[f"https://www.stepstone.de/jobs/{q}/in-deutschland?ag=age_1&sort=2&action=sort_publish" for q in Q]
        + [f"https://www.stepstone.de/work/{q}/in-germany?ag=age_1&fdl=en&sort=2&action=sort_publish" for q in Q[:6]],
        rx=r"stellenangebote--[A-Za-z0-9%-]+-\d+-inline\.html",
    ),
    "xing": dict(
        base="https://www.xing.com",
        search=[f"https://www.xing.com/jobs/search?keywords={enc(q)}&location=Germany&sort=date" for q in QS],
        rx=r"/jobs/[a-z0-9-]+-\d{6,}",
    ),
    "get_in_it": dict(
        base="https://www.get-in-it.de",
        search=[f"https://www.get-in-it.de/jobsuche?q={enc(q)}" for q in QS[:8]],
        rx=r"/jobsuche/p\d+",
    ),
    "wearedevelopers": dict(
        base="https://www.wearedevelopers.com",
        search=[f"https://www.wearedevelopers.com/en/jobs?title={enc(q)}&location=Germany" for q in QS],
        rx=r"/jobs/(?:ext/)?\d+-[a-z0-9-]+",
    ),
    "englishjobs": dict(
        base="https://englishjobs.de",
        search=[f"https://englishjobs.de/in/germany?q={enc(q)}" for q in QS],
        rx=r"/job/[a-z0-9]+-[a-z0-9]+",
    ),
    "stellenanzeigen": dict(
        base="https://www.stellenanzeigen.de",
        search=[f"https://www.stellenanzeigen.de/suche/?fulltext={enc(q)}&sort=date" for q in QS],
        rx=r"/job/[a-z0-9-]+-\d{5,}/",
    ),
    "jobware": dict(
        base="https://www.jobware.de",
        search=[f"https://www.jobware.de/jobsuche?jw_jobname={enc(q)}&jw_sort=datum" for q in QS],
        rx=r"/job/[a-z0-9-]+-\d{6,}",
    ),
    "talent": dict(
        base="https://de.talent.com",
        search=[f"https://de.talent.com/jobs?k={enc(q)}&l=Deutschland&date=1" for q in QS],
        rx=r"/view\?id=\d+",
    ),
    "zuhausejobs": dict(
        base="https://zuhausejobs.com",
        search=[f"https://zuhausejobs.com/jobs?q={enc(q)}" for q in ["developer", "entwickler", "frontend", "software"]],
        rx=r"/job/\d+-[a-z0-9-]+",
    ),
    "wellfound": dict(
        base="https://wellfound.com",
        search=[
            f"https://wellfound.com/role/l/{r}/germany"
            for r in [
                "full-stack-engineer",
                "frontend-engineer",
                "software-engineer",
                "react-developer",
                "node-js-developer",
                "artificial-intelligence-engineer",
            ]
        ],
        rx=r"/jobs/\d+-[a-z0-9-]+",
    ),
    "startup_jobs": dict(
        base="https://startup.jobs",
        search=[f"https://startup.jobs/?q={enc(q)}&loc=Germany" for q in ["full stack", "frontend", "typescript", "react", "node.js", "ai engineer"]],
        rx=r'(?<=href=")/[a-z0-9-]+-[a-z0-9-]+-\d{6,}',
    ),
    "berlinstartupjobs": dict(
        base="",
        search=["https://berlinstartupjobs.com/engineering/", "https://berlinstartupjobs.com/engineering/page/2/"],
        rx=r"https://berlinstartupjobs\.com/engineering/(?!page/|feed/)[a-z0-9-]{8,}/",
    ),
    "devjobs": dict(
        base="https://devjobs.de",
        search=[
            f"https://devjobs.de/jobs/{cat}"
            for cat in ["typescript", "react", "vue", "nodejs", "nextjs", "nestjs", "fullstack", "frontend", "webentwicklung", "ki", "llm"]
        ],
        rx=r"/job/[a-f0-9]{20,}",
    ),
}
RED_STACK = re.compile(
    r"\b(java|spring boot|kotlin|\.net|c#|golang|php|laravel|symfony|ruby on rails|scala|abap|salesforce|c\+\+|embedded|flutter|swift|react native)\b",
    re.I,
)
GOOD_STACK = re.compile(
    r"\b(typescript|javascript|react|next\.js|nextjs|vue|nuxt|node\.?js|nestjs|express|three\.js|webgl|langchain|langgraph|llm|rag)\b",
    re.I,
)
YOE = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:-|–|to|bis)?\s*(?:\d{1,2})?\s*\+?\s*(?:years|yrs|jahre)", re.I)
TITLE_OK = re.compile(
    r"full.?stack|frontend|front-end|backend|web|react|vue|node|typescript|javascript|software|developer|entwickler|engineer|\bai\b|\bki\b|llm|three",
    re.I,
)


def get(u):
    req = urllib.request.Request(u, headers=UA)
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")


def page_text(h):
    h = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))).strip()


def title_of(h):
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


def sweep_portal(name, cfg, keys, max_detail):
    sc = SeenCache("pub_" + name)
    found, stats = [], dict(search_pages=0, links=0, cached=0, red_title=0, dup=0, red_jd=0, green=0, errors=0)
    urls = []
    for su in cfg["search"]:
        try:
            h = get(su)
            stats["search_pages"] += 1
            for m in dict.fromkeys(re.findall(cfg["rx"], h)):
                u = m if m.startswith("http") else urllib.parse.urljoin(cfg["base"] or su, m)
                if u not in urls:
                    urls.append(u)
        except Exception:
            stats["errors"] += 1
        time.sleep(random.uniform(2.5, 5))
    stats["links"] = len(urls)
    for u in urls:
        if sc.seen(u):
            stats["cached"] += 1
            continue
        if stats["red_jd"] + stats["green"] + stats["red_title"] + stats["dup"] >= max_detail:
            break
        try:
            h = get(u)
        except Exception as e:
            stats["errors"] += 1
            sc.mark(u, "error", str(e)[:60])
            continue
        t = title_of(h)
        txt = page_text(h)[:20000]
        if RED_TITLE.search(t) or not TITLE_OK.search(t):
            stats["red_title"] += 1
            sc.mark(u, "red_title", t)
            time.sleep(random.uniform(2.5, 5))
            continue
        toks = re.findall(r"[a-z0-9]+", (urllib.parse.unquote(u) + " " + t).lower())
        grams = set(toks) | {a + b for a, b in zip(toks, toks[1:])}
        if is_dup_company(t, keys) or any(len(k) >= 5 and k in grams for k in keys):
            stats["dup"] += 1
            sc.mark(u, "dup", t)
            time.sleep(random.uniform(2.5, 5))
            continue
        reasons = []
        gr = german_requirement(txt)
        if gr:
            reasons.append("German: " + gr[:70])
        rs = set(x.lower() for x in RED_STACK.findall(txt))
        gs = set(x.lower() for x in GOOD_STACK.findall(txt))
        if rs and len(gs) < 2:
            reasons.append("red stack " + ",".join(sorted(rs)))
        if not gs:
            reasons.append("no TS/JS/AI stack")
        ys = [int(y) for y in YOE.findall(txt) if int(y) <= 15]
        if HARD_YOE_WORDS.search(txt) or (ys and min(ys) >= 5):
            reasons.append("YOE>=5")
        if reasons:
            stats["red_jd"] += 1
            sc.mark(u, "red", "; ".join(reasons))
        else:
            stats["green"] += 1
            sc.mark(u, "green", t)
            found.append(dict(portal=name, url=u, title=t, stack=sorted(gs), red_stack=sorted(rs), jd=txt[:8000]))
        time.sleep(random.uniform(2.5, 5))
    sc.finish()
    return name, stats, found


def main():
    max_detail = int(sys.argv[sys.argv.index("--max-detail") + 1]) if "--max-detail" in sys.argv else 60
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(PORTALS)
    keys = load_known_company_keys()
    green, allstats = [], {}
    with cf.ThreadPoolExecutor(len(only)) as ex:
        for name, stats, found in ex.map(lambda n: sweep_portal(n, PORTALS[n], keys, max_detail), only):
            allstats[name] = stats
            green += found
            print(f"{name:18} " + json.dumps(stats), flush=True)
    (H / "_public_sweep.json").write_text(json.dumps(dict(stats=allstats, green=green), ensure_ascii=False, indent=1), encoding="utf-8")
    for j in green:
        print(f"GREEN | {j['portal']} | {j['title'][:110]} | {j['url']} | stack={j['stack']} red={j['red_stack']}")


if __name__ == "__main__":
    main()
