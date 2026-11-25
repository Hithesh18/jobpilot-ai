#!/usr/bin/env bash
# One REALTIME_30M iteration (Claude Code / Gemini Antigravity shared).
# Usage: bash _agent_handoff/realtime_iter.sh
# Runs all incremental sweeps (seen_cache-filtered) and prints a compact summary of NEW candidates to inspect.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
PY="${PYTHON_EXE:-python}"
export PYTHONIOENCODING=utf-8

echo "== Bridge"
timeout 180 "$PY" bridge_ensure.py || echo "bridge check timed out (continuing; submissions may fail)"
echo "== Pending"
"$PY" retry_pending_logs.py

"$PY" -u li_sweep.py since --pages 2 > _li_sweep_since.log 2>&1 &
LI=$!
"$PY" -u ats_poll.py - 1 --json _ats_poll_1d.json > _ats_poll_1d.log 2>&1 &
AT=$!
"$PY" -u public_portals.py --max-detail 40 > _public_sweep.log 2>&1 &
PUB=$!
"$PY" -u ba_sweep.py since --max-pages 3 > _ba_since.log 2>&1

STAMP=_cdp_harvest_last.stamp
if [ ! -f "$STAMP" ] || [ $(( $(date +%s) - $(cat "$STAMP") )) -ge 1500 ]; then
  "$PY" -u harvest_all_portals.py --window 24h > _harvest_run.log 2>&1 && date +%s > "$STAMP"
  echo "(CDP portal harvest ran)" >> _harvest_run.log
else
  "$PY" -u harvest_all_portals.py --window 24h --fast-only > _harvest_run.log 2>&1
  echo "(CDP portal harvest skipped: <25 min since last, fast APIs only)" >> _harvest_run.log
fi
"$PY" screen_harvest.py latest_multi_portal_harvest.json > _harvest_screen_now.txt 2>&1
wait $LI $AT $PUB

echo "== Public portals (no login, parallel)"
grep -E '^[a-z_]+ +\{|^GREEN' _public_sweep.log | cut -c1-260
echo "== LinkedIn"
grep -E '^window|^\{|^GREEN' _li_sweep_since.log | cut -c1-230
echo "== BA"
grep -E '^\{|^GREEN' _ba_since.log | cut -c1-230
echo "== Harvest"
grep -E 'WARN|CDP\]|API/RSS\]|CDP portal harvest' _harvest_run.log | tr '\n' ' ' | cut -c1-600
echo

"$PY" - <<'EOF'
import re, json
from seen_cache import SeenCache
sc = SeenCache("harvest"); li = SeenCache("linkedin"); at = SeenCache("ats_poll")
GOOD = re.compile(r'full.?stack|frontend|front-end|backend|web|react|vue|node|typescript|javascript|software|developer|entwickler|engineer|\bai\b|\bki\b|llm', re.I)
FOREIGN = re.compile(r'arbeitnow\.(?:co\.uk|fr|ch|nl)|United States|, Spain|, France|London|Paris|Netherlands|India|United Kingdom', re.I)
print("== Harvest NEW dev titles")
for l in open('_harvest_screen_now.txt', encoding='utf-8'):
    if not l.startswith('NEW |'): continue
    p = [x.strip() for x in l.split('|')]; u = p[-1]
    m = re.search(r'jobs/view/(\d+)', u)
    if sc.seen(u) or (m and li.seen(m.group(1))): continue
    sc.mark(u, 'listed')
    if GOOD.search(p[3]) and not FOREIGN.search(l): print(l.strip()[:230])
sc.finish()
print("== ATS poll NEW")
try:
    for h in json.load(open('_ats_poll_1d.json', encoding='utf-8')):
        u = h.get('url', '')
        if at.seen(u): continue
        at.mark(u, 'listed')
        line = f"{h.get('company')} | {h.get('title')} | {h.get('location')} | {u}"
        if GOOD.search(h.get('title', '')) and not FOREIGN.search(line): print(line[:230])
except Exception as e:
    print('ats json err', e)
at.finish()
EOF
