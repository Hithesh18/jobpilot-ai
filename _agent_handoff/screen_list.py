"""Screen `_list_out.json` anchor bundles against live tracker company keys."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HANDOFF = Path(__file__).resolve().parent
sys.path.insert(0, str(HANDOFF))
from ats_poll import load_known_company_keys, norm  # noqa: E402

in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HANDOFF / "_list_out.json"
out = json.loads(in_path.read_text(encoding="utf-8"))
keys = load_known_company_keys()
seen = set()
for _u, v in out.items():
    for l in v.get("links", []):
        t = l["t"]
        nt = norm(t)
        if t in seen:
            continue
        seen.add(t)
        hit = [k for k in keys if len(k) >= 5 and k in nt]
        flag = f"DUP:{hit[0]}" if hit else "NEW"
        print(flag, "|", t[:230], "|", l["href"][:140])
