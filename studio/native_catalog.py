"""Read-only inventory of administrator-installed Gno source; never run uploaded code."""
import os
import re
from pathlib import Path
from collections import Counter

ROOTS = ("examples", "gnovm/tests/files", "gnovm/tests/stdlibs", "gno.land/pkg/integration/testdata", "gno.land/pkg/sdk/vm")
TEST = re.compile(r"(?m)^\s*func\s+(Test[A-Z_a-z0-9]+)\s*\(")
FUNC = re.compile(r"(?m)^\s*func\s+([A-Z][A-Za-z0-9_]*)\s*\(")

def inventory(root=None):
    root = Path(root or os.environ.get("GNOROOT") or Path.home()/".gno/source").resolve()
    rows = []
    for scope in ROOTS:
        folder = root / scope
        if not folder.is_dir() or not folder.resolve().is_relative_to(root):
            continue
        for directory, dirs, files in os.walk(folder, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            for name in sorted(files):
                if not name.endswith(("_test.gno", "_filetest.gno", "_test.go")) and not (scope == "gnovm/tests/files" and name.endswith(".gno")):
                    continue
                path = Path(directory)/name
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    continue
                try:
                    if path.stat().st_size > 512000:
                        continue
                    source = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    continue
                kind = "go" if name.endswith(".go") else "filetest" if name.endswith("_filetest.gno") or scope == "gnovm/tests/files" else "gno"
                names = TEST.findall(source)
                if kind == "filetest" and not names:
                    names = [name]
                for test in names:
                    rows.append({"scope":scope,"package":str(path.parent.relative_to(root)),"file":str(path.relative_to(root)),"name":test,"kind":kind})
                    if len(rows) >= 20000:
                        return rows, True
    return rows, False

def summarize(rows):
    return {"tests":len(rows),"packages":len({r["package"] for r in rows}),"files":len({r["file"] for r in rows}),"kinds":dict(Counter(r["kind"] for r in rows))}
