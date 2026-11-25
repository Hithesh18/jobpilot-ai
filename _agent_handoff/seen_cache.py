r"""
Shared incremental-sweep cache (Claude Code + Gemini Antigravity). Avoids re-screening the same postings.

  _seen_jobs.json  = {portal: {job_id: {"first_seen": iso, "verdict": "green|red|dup|red_title", "why": str}}}
  sweep_state.json -> "portal_last_sweep": {portal: iso}   (timestamp of the last finished sweep per portal)

Usage in a sweeper:
  from seen_cache import SeenCache
  sc = SeenCache("linkedin")
  hours = sc.hours_since_last(default=24)   # window to request from the portal (+1h overlap)
  if sc.seen(jid): skip                     # no JD fetch for already-screened postings
  sc.mark(jid, "red", "German required")
  sc.finish()                               # saves cache + stamps portal_last_sweep
"""
import datetime as dt
import json
import math
import os
import threading
import time
from pathlib import Path

H = Path(__file__).resolve().parent
CACHE = H / "_seen_jobs.json"
STATE = H / "sweep_state.json"
KEEP_DAYS = 30
_FILE_LOCK = threading.Lock()


def _now():
    return dt.datetime.now().astimezone()


class SeenCache:
    def __init__(self, portal):
        self.portal = portal
        self.started = _now()
        try:
            self.all = json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            self.all = {}
        self.d = self.all.setdefault(portal, {})
        cutoff = (self.started - dt.timedelta(days=KEEP_DAYS)).isoformat()
        for k in [k for k, v in self.d.items() if v.get("first_seen", "") < cutoff]:
            del self.d[k]
        self.new = 0

    def last_sweep(self):
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
            return dt.datetime.fromisoformat(st.get("portal_last_sweep", {})[self.portal])
        except Exception:
            return None

    def hours_since_last(self, default=24, cap=24):
        """Hours to request: time since the last finished sweep + 1h overlap, capped (default if never swept)."""
        last = self.last_sweep()
        if not last:
            return default
        return max(1, min(cap, math.ceil((self.started - last).total_seconds() / 3600) + 1))

    def seen(self, jid):
        return str(jid) in self.d

    def mark(self, jid, verdict, why=""):
        jid = str(jid)
        if jid not in self.d:
            self.new += 1
        self.d[jid] = dict(
            first_seen=self.d.get(jid, {}).get("first_seen", self.started.isoformat(timespec="seconds")),
            verdict=verdict,
            why=(why or "")[:120],
        )

    def save(self):
        with _FILE_LOCK:
            cur = {}
            for _ in range(5):
                try:
                    cur = json.loads(CACHE.read_text(encoding="utf-8"))
                    break
                except Exception:
                    time.sleep(0.1)
            mine = cur.get(self.portal, {})
            mine.update(self.d)
            cur[self.portal] = mine
            self.d = mine
            tmp = CACHE.with_suffix(f".{self.portal}.{os.getpid()}.tmp")
            tmp.write_text(json.dumps(cur, ensure_ascii=False, indent=0), encoding="utf-8")
            for _ in range(5):
                try:
                    tmp.replace(CACHE)
                    break
                except PermissionError:
                    time.sleep(0.1)

    def finish(self):
        self.save()
        with _FILE_LOCK:
            st = None
            for _ in range(5):
                try:
                    st = json.loads(STATE.read_text(encoding="utf-8"))
                    break
                except Exception:
                    time.sleep(0.15)
            if isinstance(st, dict):
                st.setdefault("portal_last_sweep", {})[self.portal] = self.started.isoformat(timespec="seconds")
                tmp_st = STATE.with_suffix(f".{self.portal}.{os.getpid()}.tmp")
                tmp_st.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
                for _ in range(5):
                    try:
                        tmp_st.replace(STATE)
                        break
                    except PermissionError:
                        time.sleep(0.15)
