r"""Read LinkedIn job descriptions via the PUBLIC guest API (no cookies, not tied to the user's account).
Usage: python _agent_handoff/li_jd.py <job_id_or_url> [...] -> prints title/company/posted + full JD text (throttled 3-5 s)."""
import html
import random
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()


for i, a in enumerate(sys.argv[1:]):
    jid = re.search(r"(\d{6,})", a).group(1)
    h = (
        urllib.request.urlopen(
            urllib.request.Request(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}", headers={"User-Agent": UA}),
            timeout=20,
        )
        .read()
        .decode("utf-8", "ignore")
    )
    t = re.search(r"top-card-layout__title[^>]*>(.*?)</h2>", h, re.S)
    c = re.search(r"topcard__org-name-link[^>]*>(.*?)</a>", h, re.S)
    p = re.search(r"posted-time-ago__text[^>]*>(.*?)</span>", h, re.S)
    m = re.search(r"show-more-less-html__markup[^>]*>(.*?)</div>", h, re.S)
    print(
        f"===== {jid} | {clean(t.group(1)) if t else ''} | {clean(c.group(1)) if c else ''} | {clean(p.group(1)) if p else ''}\n"
        f"{clean(m.group(1)) if m else '(no JD)'}\n"
    )
    if i < len(sys.argv) - 2:
        time.sleep(random.uniform(3, 5))
