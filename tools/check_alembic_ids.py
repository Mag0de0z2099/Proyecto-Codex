import pathlib
import re
import sys

ok = True
for path in pathlib.Path("migrations/versions").glob("*.py"):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^revision\s*=\s*'([^']+)'", text, re.M)
    if match and len(match.group(1)) > 32:
        print(f"[ERROR] {path}: revision '{match.group(1)}' > 32 chars")
        ok = False
if not ok:
    sys.exit(1)
