"""Clean plain-text extraction helper for Cover Letter PDFs."""
import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
idx = t.find("Dear")
if idx >= 0:
    t = t[idx:]
t = re.sub(r"\b([B-HJ-Z]) ([a-z])", r"\1\2", t).replace("\u223c", "~").replace(" ,", ",").replace(" .", ".")
paras = []
cur = []
for line in t.split("\n"):
    s = line.strip()
    if not s:
        continue
    cur.append(s)
    if s.endswith((",", ".")) and (len(s) < 95 or s.startswith("Dear") or s.startswith("Best regards") or s.startswith("Sincerely")):
        paras.append(" ".join(cur))
        cur = []
if cur:
    paras.append(" ".join(cur))
out = "\n\n".join(paras).replace("multi- tenant", "multi-tenant").replace("- ", "-")
p.with_name(p.stem + "_clean.txt").write_text(out, encoding="utf-8")
print(out)
