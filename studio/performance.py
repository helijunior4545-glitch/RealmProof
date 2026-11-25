"""Bounded local process benchmarks; timings are observations, not SLAs."""
import hashlib
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path
from time import monotonic_ns
from .ledger_lab import diagnostic_excerpt
from .services import evaluate

COUNT = 90
GROUPS = {"latency": 20, "throughput": 20, "scalability": 15,
          "gas": 15, "stability": 10, "startup": 10}

def plan():
    rows = []
    for category, count in GROUPS.items():
        for i in range(count):
            n = {"latency": 1, "throughput": 100,
                 "scalability": [1, 10, 50, 100, 200][i % 5],
                 "gas": [1, 10, 100][i % 3],
                 "stability": 50, "startup": 0 if i % 2 == 0 else 1}[category]
            rows.append((category, i, n))
    return rows

def harness_for(n):
    return '''package ledger
import "testing"
import "fmt"
func TestPerformance(t *testing.T) {
    valid := true
    for i := 0; i < %d; i++ {
        a := Deposit(10)
        b := Reserve(10, true)
        c := Settle(10, true)
        valid = a && b && c && Balance() == 0 && Held() == 0 && Paid() == (i+1)*10 && valid
    }
    fmt.Println("RP_PERF", valid, Paid())
}
''' % n

def parse_output(output, n):
    matches = re.findall(r"(?m)^\s*RP_PERF (true|false) ([0-9]+)\s*$", output)
    if len(matches) != 1:
        raise RuntimeError("Incomplete performance evidence: " + diagnostic_excerpt(output))
    ok, paid = matches[0]
    gas = re.findall(r"\bGAS:\s*([0-9]+)\b", output)
    return {"valid": ok == "true" and int(paid) == n*10,
            "gas": int(gas[0]) if len(gas) == 1 else None}

def summarize(samples):
    ordered = sorted(samples)
    if not ordered:
        raise ValueError("No samples")
    def percentile(p):
        return ordered[max(0, math.ceil(p*len(ordered))-1)]
    return {"samples": len(ordered), "p50_ms": statistics.median(ordered),
            "p95_ms": percentile(.95), "p99_ms": percentile(.99),
            "stdev_ms": statistics.pstdev(ordered)}

def measure(binary, source, n, env, deadline):
    harness = harness_for(n)
    with tempfile.TemporaryDirectory(prefix="rp-performance-") as directory:
        path = Path(directory)
        (path / "ledger.gno").write_text(source)
        (path / "ledger_test.gno").write_text(harness)
        (path / "gnomod.toml").write_text('module = "gno.land/r/realmproof/ledger"\n')
        (path / "gno.mod").write_text("module gno.land/r/realmproof/ledger\n")
        remaining = (deadline-monotonic_ns())/1e9
        if remaining <= 0:
            raise RuntimeError("Performance campaign deadline exceeded.")
        start = monotonic_ns()
        result = subprocess.run([binary, "test", "-v", "."], cwd=path, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=min(15, remaining))
        elapsed = (monotonic_ns()-start)/1e6
    if result.returncode:
        raise RuntimeError("Performance runtime error: " + diagnostic_excerpt(result.stdout))
    observation = parse_output(result.stdout, n)
    return observation, elapsed, hashlib.sha256(harness.encode()).hexdigest()

def run(progress=None):
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI unavailable.")
    source = (Path(__file__).resolve().parent.parent / "realms/ledger/ledger.gno").read_text()
    env = os.environ.copy()
    root = Path.home() / ".gno/source"
    if not env.get("GNOROOT") and (root / "gnovm/stdlibs").is_dir():
        env["GNOROOT"] = str(root)
    deadline = monotonic_ns() + 480*10**9
    rows = []
    for category, index, n in plan():
        observation, elapsed, harness_hash = measure(binary, source, n, env, deadline)
        if category == "gas" and observation["gas"] is None:
            raise RuntimeError("Gno gas measurement unavailable in runtime output.")
        expected = {"valid": True}
        observed = {"valid": observation["valid"]}
        rows.append({"name": f"Performance / {category} / {index}", "expected": expected,
                     "observed": observed, "verdict": evaluate(expected, observed).status,
                     "evidence": {"type": "local_gno", "verified_on_chain": False,
                                  "category": category, "cycles": n, "operations": n*3,
                                  "elapsed_ms": elapsed, "gas": observation["gas"],
                                  "operations_per_second": n*3000/elapsed if elapsed > 0 else None,
                                  "timing_scope": "cli_process_wall_time",
                                  "platform": platform.system(), "architecture": platform.machine(),
                                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                  "harness_sha256": harness_hash}})
        if progress:
            progress(len(rows))
    for row in rows:
        e = row["evidence"]
        e["same_workload_statistics"] = summarize([r["evidence"]["elapsed_ms"] for r in rows
            if r["evidence"]["category"] == e["category"] and r["evidence"]["cycles"] == e["cycles"]])
    return rows
