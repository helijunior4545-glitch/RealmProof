"""Differential observations against a bundled historical ledger snapshot."""
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from .security_campaign import campaign, GROUPS, SEED
from .ledger_lab import diagnostic_excerpt
from .services import evaluate

COUNT = 300
BASELINE_COMMIT = "190a8baac74c3234dbfdeb4279885362898be7a5"

def cases():
    selected = []
    seen = {}
    for case in campaign():
        group = case["input"]["category"]
        seen[group] = seen.get(group, 0) + 1
        if seen[group] <= GROUPS[group] // 2:
            selected.append(case)
    return selected

def harness_for(batch):
    lines = ['package ledger', 'import "testing"', 'import "fmt"', 'func TestRegression(t *testing.T) {']
    for case in batch:
        key = case["id"]
        lines += ["{", *case["setup"][:5],
                  f'fmt.Println("RP_TRACE {key} 0", initial, Balance(), Held(), Paid())']
        for j, statement in enumerate(case["setup"][6::2]):
            lines += [statement, f'fmt.Println("RP_TRACE {key} {j+1}", step{j}, Balance(), Held(), Paid())']
        lines += ["}"]
    return "\n".join(lines + ["}", ""])

def parse_output(output, batch):
    matches = re.findall(r"(?m)^\s*RP_TRACE ([0-9]+) ([0-9]+) (true|false) (-?[0-9]+) (-?[0-9]+) (-?[0-9]+)\s*$", output)
    expected = [(c["id"], j) for c in batch for j in range(len(c["input"]["operations"])+1)]
    if [(int(k), int(j)) for k,j,*_ in matches] != expected:
        raise RuntimeError("Incomplete regression trace: " + diagnostic_excerpt(output))
    traces = {c["id"]: [] for c in batch}
    for k,j,ok,a,h,p in matches:
        traces[int(k)].append({"accepted": ok == "true", "available": int(a), "held": int(h), "paid": int(p)})
    return traces

def observe(binary, source, harness, batch, env):
    with tempfile.TemporaryDirectory(prefix="rp-regression-") as directory:
        path = Path(directory)
        (path / "ledger.gno").write_text(source)
        (path / "ledger_test.gno").write_text(harness)
        (path / "gnomod.toml").write_text('module = "gno.land/r/realmproof/ledger"\n')
        (path / "gno.mod").write_text("module gno.land/r/realmproof/ledger\n")
        result = subprocess.run([binary, "test", "-v", "."], cwd=path, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=20)
    if result.returncode:
        raise RuntimeError("Regression runtime error: " + diagnostic_excerpt(result.stdout))
    return parse_output(result.stdout, batch)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def compare(case, baseline, current, evidence):
    expected, observed = {"trace": baseline}, {"trace": current}
    differences = [{"step": i, "fields": [k for k in old if old[k] != new[k]]}
                   for i, (old, new) in enumerate(zip(baseline, current)) if old != new]
    return {"name": f"Regression / {case['id']}", "expected": expected, "observed": observed,
            "verdict": evaluate(expected, observed).status,
            "evidence": {**evidence, "input": case["input"], "case_id": case["id"],
                         "classification": "behavior_changed" if baseline != current else "unchanged",
                         "differences": differences}}

def run(progress=None):
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI unavailable.")
    root = Path(__file__).resolve().parent.parent / "realms"
    baseline = (root / "baselines/ledger-v3.gno").read_text()
    current = (root / "ledger/ledger.gno").read_text()
    env = os.environ.copy()
    gno_root = Path.home() / ".gno/source"
    if not env.get("GNOROOT") and (gno_root / "gnovm/stdlibs").is_dir():
        env["GNOROOT"] = str(gno_root)
    selected = cases()
    rows = []
    for offset in range(0, len(selected), 50):
        batch = selected[offset:offset+50]
        harness = harness_for(batch)
        old = observe(binary, baseline, harness, batch, env)
        new = observe(binary, current, harness, batch, env)
        evidence = {"type": "local_gno", "verified_on_chain": False, "seed": SEED,
                    "baseline_commit": BASELINE_COMMIT, "baseline_sha256": digest(baseline),
                    "source_sha256": digest(current), "harness_sha256": digest(harness)}
        rows.extend(compare(c, old[c["id"]], new[c["id"]], evidence) for c in batch)
        if progress:
            progress(len(rows))
    return rows
