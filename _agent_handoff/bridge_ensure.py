r"""Ensure the CDP bridge on 127.0.0.1:9333 is up AND connected to Chrome; start it in background if not."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

H = Path(__file__).resolve().parent
PING = H / "cdp_scripts" / "_ping.js"
BRIDGE_JS = H / "cdp_bridge.js"


def healthy():
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:9333/",
            data=json.dumps({"scriptPath": str(PING)}).encode(),
            headers={"Content-Type": "application/json"},
        )
        r = json.loads(urllib.request.urlopen(req, timeout=45).read())
        return bool(r.get("ok") and r["result"]["connected"] and r["result"]["contexts"] > 0)
    except Exception:
        return False


def http_up():
    try:
        return urllib.request.urlopen("http://127.0.0.1:9333/", timeout=5).status == 200
    except Exception:
        return False


for _ in range(3):
    if healthy():
        print("bridge: ok")
        sys.exit(0)
    time.sleep(5)

if http_up() and "--force" not in sys.argv:
    print("bridge: process up (browser busy) - skipping restart to avoid re-prompting Chrome permission")
    sys.exit(0)

log_out = open(H / "_bridge.log", "a", encoding="utf-8")
log_err = open(H / "_bridge.err", "a", encoding="utf-8")
kwargs = {"stdout": log_out, "stderr": log_err, "cwd": str(H.parent)}
if os.name == "nt":
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
else:
    kwargs["start_new_session"] = True
subprocess.Popen(["node", str(BRIDGE_JS)], **kwargs)

for _ in range(12):
    time.sleep(5)
    if healthy():
        print("bridge: started ok")
        sys.exit(0)
print("bridge: START FAILED (ensure Chrome is running with --remote-debugging-port=9222 or chrome://inspect/#remote-debugging)")
