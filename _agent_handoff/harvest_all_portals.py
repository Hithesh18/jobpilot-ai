r"""
Multi-Portal Job Harvester (Cross-Platform Native Python + Silent Background Chrome CDP Bridge — ZERO Popups!)
Covers ALL 21+ Job Portals + Direct Multi-ATS APIs & Startpage/Yahoo Search:
  Fast Official JSON / RSS APIs (Zero CAPTCHA):
    1. LinkedIn Paginated Guest API (opt-in via HARVEST_LI=1; covered primarily by throttled li_sweep.py)
    2. Arbeitnow JSON API (pages 1-3)
    3. Bundesagentur fuer Arbeit (BA Jobsuche Official REST API `pc/v6/jobs`)
    4. Workable Global Germany API (`jobs.workable.com/api/v1/jobs`)
    5. GermanTechJobs Official Full XML RSS (`germantechjobs.de/rss`)
    6. BerlinStartupJobs Engineering RSS (`berlinstartupjobs.com/engineering/feed/`)
  Background Chrome CDP Portals (`http://127.0.0.1:9333` via `s_portals_cdp.js` + `s_sp.js`):
    7. StepStone.de (`fdl=en`)          15. JobMESH.de
    8. Indeed Germany (`de.indeed.com`) 16. Staufenbiel / Absolventa
    9. stellenanzeigen.de               17. Truffls.de
   10. Yourfirm.de                      18. Zuhausejobs.com
   11. Jobware.de                       19. Jobvector.de
   12. XING Jobs                        20. Talent.com / Monster / Joblift / Glassdoor DE
   13. EnglishJobs.de                   21. Welcome to the Jungle / Relocate.me / Himalayas
   14. get-in-IT.de & WeAreDevelopers & Make it in Germany

Usage:
  Tier 1 (<24h):  python _agent_handoff/harvest_all_portals.py --window 24h
  Tier 2 (<64h):  python _agent_handoff/harvest_all_portals.py --window 64h
  Backlog (14d):  python _agent_handoff/harvest_all_portals.py --window 14d
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

HANDOFF = Path(__file__).resolve().parent
ROOT = HANDOFF.parent
OUT_JSON = HANDOFF / "latest_multi_portal_harvest.json"
sys.path.insert(0, str(HANDOFF))
from ats_poll import poll_global_workable, poll_rss_feeds  # noqa: E402


def build_cdp_portal_specs(window: str) -> dict:
    st_age = "age_1" if window == "24h" else ("age_3" if window == "64h" else "age_14")
    ind_age = "1" if window == "24h" else ("3" if window == "64h" else "14")
    jm_age = "1" if window == "24h" else ("3" if window == "64h" else "14")
    tal_age = "1" if window == "24h" else ("3" if window == "64h" else "14")
    pages = range(1, 3) if window == "24h" else range(1, 5)

    return {
        "StepStone_EN": {
            "re": r"stellenangebote--",
            "scroll": 2,
            "urls": [
                f"https://www.stepstone.de/work/junior-full-stack-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page={p}"
                for p in pages
            ]
            + [
                f"https://www.stepstone.de/work/junior-frontend-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/junior-software-engineer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/react-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/vue-js-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/typescript-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/node-js-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/web-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
                f"https://www.stepstone.de/work/full-stack-developer/in-germany?ag={st_age}&fdl=en&sort=2&action=sort_publish&page=1",
            ],
        },
        "Indeed_DE": {
            "re": r"viewjob\?jk=",
            "scroll": 1,
            "urls": [
                f"https://de.indeed.com/jobs?q=(%22Junior+Full+Stack%22+OR+%22Junior+Frontend%22+OR+%22Junior+Software+Engineer%22+OR+%22Mid-Level+Full+Stack%22)+-Senior+-Principal+-Staff&l=Deutschland&fromage={ind_age}&sort=date&start={s}"
                for s in ((0, 10) if window == "24h" else (0, 10, 20, 30))
            ]
            + [
                f"https://de.indeed.com/jobs?q=(%22React+Developer%22+OR+%22Vue.js+Developer%22+OR+%22TypeScript+Developer%22+OR+%22Node.js+Developer%22+OR+%22Web+Developer%22+OR+%22Junior+AI+Engineer%22)+-Senior+-Staff&l=Deutschland&fromage={ind_age}&sort=date&start=0"
            ],
        },
        "XING_Jobs": {
            "re": r"xing\.com/jobs/[a-z0-9-]+-\d+",
            "scroll": 4,
            "urls": [
                "https://www.xing.com/jobs/search?keywords=Junior%20Full%20Stack%20Developer&location=Germany&sort=date",
                "https://www.xing.com/jobs/search?keywords=Junior%20Frontend%20Developer&location=Germany&sort=date",
                "https://www.xing.com/jobs/search?keywords=React%20TypeScript%20Developer&location=Germany&sort=date",
                "https://www.xing.com/jobs/search?keywords=Vue.js%20Node.js%20Developer&location=Germany&sort=date",
                "https://www.xing.com/jobs/search?keywords=Junior%20AI%20Engineer&location=Germany&sort=date",
            ],
        },
        "EnglishJobs_de": {
            "re": r"englishjobs\.de/jobs/",
            "scroll": 1,
            "urls": [f"https://englishjobs.de/jobs/junior_software_engineer?sort=date&page={p}" for p in pages]
            + [
                "https://englishjobs.de/jobs/full_stack_developer?sort=date&page=1",
                "https://englishjobs.de/jobs/react_developer?sort=date&page=1",
                "https://englishjobs.de/jobs/vue_js?sort=date&page=1",
                "https://englishjobs.de/jobs/typescript?sort=date&page=1",
                "https://englishjobs.de/jobs/web_developer?sort=date&page=1",
            ],
        },
        "WeAreDevelopers": {
            "re": r"wearedevelopers\.com/en/jobs/",
            "scroll": 2,
            "urls": [
                "https://www.wearedevelopers.com/en/jobs?q=Junior%20Full%20Stack&country=Germany",
                "https://www.wearedevelopers.com/en/jobs?q=React%20Developer&country=Germany",
                "https://www.wearedevelopers.com/en/jobs?q=Vue&country=Germany",
                "https://www.wearedevelopers.com/en/jobs?q=TypeScript%20Developer&country=Germany",
            ],
        },
        "Make_it_in_Germany": {
            "re": r"make-it-in-germany\.com/en/working-in-germany/job-listings/job/job-",
            "scroll": 2,
            "urls": [
                "https://www.make-it-in-germany.com/en/working-in-germany/job-listings?tx_solr%5Bq%5D=Junior+Software+Engineer",
                "https://www.make-it-in-germany.com/en/working-in-germany/job-listings?tx_solr%5Bq%5D=Full+Stack+Developer",
                "https://www.make-it-in-germany.com/en/working-in-germany/job-listings?tx_solr%5Bq%5D=Web+Developer",
            ],
        },
        "get_in_IT": {
            "re": r"get-in-it\.de/jobsuche/p\d+",
            "scroll": 4,
            "urls": [
                "https://www.get-in-it.de/jobsuche?q=Junior%20Full%20Stack",
                "https://www.get-in-it.de/jobsuche?q=Junior%20Frontend",
                "https://www.get-in-it.de/jobsuche?q=React%20Developer",
                "https://www.get-in-it.de/jobsuche?q=Vue.js",
                "https://www.get-in-it.de/jobsuche?q=TypeScript%20Developer",
                "https://www.get-in-it.de/jobsuche?q=Junior%20AI%20Engineer",
            ],
        },
        "Jobvector": {
            "re": r"jobvector\.de/job/|jobvector\.de/stellenangebote/",
            "scroll": 3,
            "urls": [
                "https://www.jobvector.de/jobs/junior-software-developer/",
                "https://www.jobvector.de/jobs/full-stack-developer/",
                "https://www.jobvector.de/jobs/web-developer/",
                "https://www.jobvector.de/jobs/artificial-intelligence/",
            ],
        },
        "stellenanzeigen_Yourfirm_Jobware_JobMESH": {
            "re": r"(stellenanzeigen\.de/job/|yourfirm\.de/job/|jobware\.de/job/|jobmesh\.de/job)",
            "scroll": 2,
            "urls": [
                "https://www.stellenanzeigen.de/suche/?fulltext=Junior+Full+Stack+Developer&sort=date",
                "https://www.yourfirm.de/suche/junior-software-engineer/",
                "https://www.jobware.de/jobsuche?jw_jobname=Junior+Full+Stack+Developer&jw_ort=Deutschland&jw_sort=datum",
                f"https://www.jobmesh.de/jobs?q=Junior+Full+Stack+Developer&l=Deutschland&d={jm_age}",
            ],
        },
        "Talent_Monster_Joblift_Zuhause_Truffls_Staufenbiel": {
            "re": r"(de\.talent\.com/view\?id=|monster\.de/stellenangebote/|joblift\.de/details/|zuhausejobs\.com/stellenangebote/|zuhausejobs\.com/job|truffls\.de/.*job|absolventa\.de/jobs/\d+)",
            "scroll": 3,
            "urls": [
                f"https://de.talent.com/jobs?k=Junior+Full+Stack+Developer&l=Germany&date={tal_age}",
                f"https://de.talent.com/jobs?k=React+TypeScript+Developer&l=Germany&date={tal_age}",
                "https://zuhausejobs.com/?s=Full+Stack+Developer",
                "https://www.truffls.de/jobs",
                "https://www.absolventa.de/jobs/berufsfeld-it-softwareentwicklung",
            ],
        },
        "WTTJ_Otta_Relocate_Himalayas": {
            "re": r"(welcometothejungle\.com/[a-z]{2}/companies/[a-z0-9-]+/jobs/[a-z0-9_-]+|relocate\.me/[a-z-]+/[a-z0-9-]+/[a-z0-9-]+-\d+|himalayas\.app/companies/[a-z0-9-]+/jobs/[a-z0-9-]+)",
            "scroll": 3,
            "urls": [
                "https://www.welcometothejungle.com/en/jobs?query=full%20stack&refinementList%5Boffices.country_code%5D%5B%5D=DE&sortBy=mostRecent",
                "https://www.welcometothejungle.com/en/jobs?query=frontend&refinementList%5Boffices.country_code%5D%5B%5D=DE&sortBy=mostRecent",
                "https://relocate.me/search?country=germany&query=full%20stack",
                "https://relocate.me/search?country=germany&query=frontend",
                "https://himalayas.app/jobs/countries/germany/full-stack-developer",
            ],
        },
        "Glassdoor_DE": {
            "re": r"glassdoor\.de/(?:job-listing|partner/jobListing\.htm|Stellen/)[^\"'\s]+",
            "scroll": 2,
            "urls": [
                "https://www.glassdoor.de/Job/deutschland-full-stack-developer-jobs-SRCH_IL.0,11_IN96_KO12,32.htm?fromAge=1&sortBy=date_desc",
                "https://www.glassdoor.de/Job/deutschland-frontend-developer-jobs-SRCH_IL.0,11_IN96_KO12,30.htm?fromAge=1&sortBy=date_desc",
                "https://www.glassdoor.de/Job/deutschland-react-developer-jobs-SRCH_IL.0,11_IN96_KO12,27.htm?fromAge=1&sortBy=date_desc",
            ],
        },
    }


def fetch_http(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"},
    )
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="ignore")


def harvest_fast_apis(window: str) -> dict:
    days = 1 if window == "24h" else (3 if window == "64h" else 14)
    tpr = "r86400" if window == "24h" else ("r259200" if window == "64h" else "r1209600")
    cut = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)

    results = {
        "linkedin": [],
        "arbeitnow": [],
        "workable_de": [],
        "germantechjobs": [],
        "berlinstartupjobs": [],
        "arbeitsagentur_ba": [],
    }

    for src, comp, title, loc, pub, url in poll_global_workable(days) + poll_rss_feeds(cut):
        bucket = "workable_de" if src == "workable" else src
        if bucket in results:
            results[bucket].append({"company": comp, "title": title, "location": loc, "url": url})

    ba_headers = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Mozilla/5.0"}
    seen_ba = set()
    for q in ("Full Stack Engineer", "Frontend Engineer", "TypeScript", "AI Engineer", "Software Engineer English"):
        try:
            r = requests.get(
                "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs",
                params={"was": q, "veroeffentlichtseit": str(days), "size": 50, "page": 1, "angebotsart": 1},
                headers=ba_headers,
                timeout=12,
            )
            if r.ok:
                for j in r.json().get("ergebnisliste", []):
                    ref = j.get("referenznummer")
                    if not ref or ref in seen_ba:
                        continue
                    seen_ba.add(ref)
                    loc = ((j.get("stellenlokationen") or [{}])[0].get("adresse") or {}).get("ort", "Germany")
                    results["arbeitsagentur_ba"].append(
                        {
                            "company": j.get("firma") or "",
                            "title": j.get("stellenangebotsTitel") or "",
                            "location": loc,
                            "url": j.get("externeUrl") or f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
                        }
                    )
        except Exception:
            pass

    queries = [
        "Junior Full Stack NOT Senior NOT Principal NOT Staff",
        "Junior Frontend NOT Senior NOT Principal NOT Staff",
        "Junior Software Engineer NOT Senior NOT Principal NOT Staff",
        "Mid-Level Full Stack NOT Principal NOT Staff",
        "React Developer NOT Senior NOT Principal NOT Staff",
        "Vue.js Developer NOT Senior NOT Principal NOT Staff",
        "TypeScript Developer NOT Senior NOT Principal NOT Staff",
        "Node.js Developer NOT Senior NOT Principal NOT Staff",
        "Web Developer TypeScript NOT Senior",
        "Junior AI Engineer NOT Senior NOT Staff",
    ]
    seen_li = set()
    if os.environ.get("HARVEST_LI") != "1":
        queries = []
    for q in queries:
        for st in (0, 25, 50, 75, 100):
            u = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={urllib.parse.quote(q)}"
                f"&location=Germany&geoId=101282230&f_TPR={tpr}&sortBy=DD&start={st}"
            )
            try:
                html = fetch_http(u, timeout=8)
                matches = list(
                    re.finditer(
                        r'data-entity-urn="urn:li:jobPosting:(\d+)".*?<h3 class="base-search-card__title">\s*(.*?)\s*</h3>.*?<h4 class="base-search-card__subtitle">(.*?)</h4>.*?<span class="job-search-card__location">\s*(.*?)\s*</span>',
                        html,
                        re.S,
                    )
                )
                if not matches:
                    break
                for m in matches:
                    jid = m.group(1)
                    if jid in seen_li:
                        continue
                    seen_li.add(jid)
                    results["linkedin"].append(
                        {
                            "jid": jid,
                            "title": re.sub(r"\s+", " ", m.group(2)).strip(),
                            "company": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(3))).strip(),
                            "location": re.sub(r"\s+", " ", m.group(4)).strip(),
                            "url": f"https://www.linkedin.com/jobs/view/{jid}/",
                        }
                    )
            except Exception:
                break
    return results


def harvest_cdp_portals(window: str) -> dict:
    specs = build_cdp_portal_specs(window)
    cfg_path = HANDOFF / "_portals_cdp_cfg.json"
    out_path = HANDOFF / "_portals_cdp_out.json"
    cfg_path.write_text(json.dumps({"window": window, "portals": specs}, indent=2), encoding="utf-8")

    try:
        ping = requests.get("http://127.0.0.1:9333", timeout=3)
        if ping.ok:
            script_path = str((HANDOFF / "cdp_scripts" / "s_portals_cdp.js").resolve())
            r = requests.post("http://127.0.0.1:9333", json={"scriptPath": script_path}, timeout=900)
            if r.ok and out_path.exists():
                return json.loads(out_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"WARN: CDP bridge harvest fallback ({e})", file=sys.stderr)

    from headless_browser import launch_silent_context
    from playwright.sync_api import sync_playwright

    harvested = {}
    with sync_playwright() as p:
        ctx = launch_silent_context(p)
        page = ctx.new_page()
        for portal, spec in specs.items():
            harvested[portal] = []
            for u in spec["urls"]:
                try:
                    page.goto(u, wait_until="domcontentloaded", timeout=16000)
                    page.wait_for_timeout(1500)
                    links = page.evaluate(
                        """() => Array.from(document.querySelectorAll('a[href]'))
                            .map(a => ({ href: a.href, text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 160) }))
                            .filter(x => x.text.length > 10 && /engineer|developer|stack|frontend|backend|typescript|react|vue|node|ai|software/i.test(x.text + ' ' + x.href))
                            .slice(0, 40)"""
                    )
                    harvested[portal].extend(links)
                except Exception:
                    pass
        page.close()
        ctx.close()
    return harvested


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", choices=["24h", "64h", "14d"], default="24h")
    ap.add_argument("--list-portals", action="store_true")
    ap.add_argument("--fast-only", action="store_true", help="Run only fast JSON/RSS APIs without CDP browser")
    args = ap.parse_args()

    specs = build_cdp_portal_specs(args.window)
    if args.list_portals:
        print(f"Configured 6 Fast Official JSON/RSS APIs + {len(specs)} CDP Portal Groups for window={args.window}:")
        for k in ("linkedin", "arbeitnow", "workable_de", "germantechjobs", "berlinstartupjobs", "arbeitsagentur_ba"):
            print(f"  [API/RSS] {k}")
        for k, v in specs.items():
            print(f"  [CDP]     {k} ({len(v['urls'])} search URLs)")
        return

    data = {
        "harvested_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "window": args.window,
        "fast_apis": harvest_fast_apis(args.window),
        "german_portals": {} if args.fast_only else harvest_cdp_portals(args.window),
    }
    OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved multi-portal harvest ({args.window}) -> {OUT_JSON}")
    for k, v in data["fast_apis"].items():
        print(f"  [API/RSS] {k}: {len(v)} items")
    for k, v in data["german_portals"].items():
        print(f"  [CDP]     {k}: {len(v)} candidate job links")


if __name__ == "__main__":
    main()
