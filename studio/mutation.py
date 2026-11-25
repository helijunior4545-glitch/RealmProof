"""Trusted first-order ledger mutants. Runtime errors never count as kills."""
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from .specialized import campaign, harness_for, parse_output
from .ledger_lab import diagnostic_excerpt
from .services import evaluate

# Each replacement is scoped to a single named function.
RULES = {
    "Deposit": [("frozen || ", ""), ("amount <= 0", "amount < 0"),
                ("amount <= 0", "amount <= 1"), ("amount > 1000000000-available-held-paid", "amount > 1000000000"),
                ("available += amount", "available -= amount"), ("available += amount", "available += amount + 1")],
    "Reserve": [("frozen || ", ""), ("!authorized || ", ""), ("amount <= 0", "amount < 0"),
                ("amount > available", "amount >= available"), ("amount > available", "amount > available+1"),
                ("available -= amount", "available += amount"), ("held += amount", "held -= amount"),
                ("held += amount", "held += amount+1")],
    "Release": [("frozen || ", ""), ("!authorized || ", ""), ("amount <= 0", "amount < 0"),
                ("amount > held", "amount >= held"), ("amount > held", "amount > held+1"),
                ("held -= amount", "held += amount"), ("available += amount", "available -= amount"),
                ("available += amount", "available += amount+1")],
    "Settle": [("frozen || ", ""), ("!authorized || ", ""), ("amount <= 0", "amount < 0"),
                ("amount > held", "amount >= held"), ("amount > held", "amount > held+1"),
                ("held -= amount", "held += amount"), ("paid += amount", "paid -= amount"),
                ("paid += amount", "paid += amount+1")],
    "Freeze": [("frozen = value", "frozen = !value"), ("frozen = value", "frozen = false")],
}
COUNT = sum(map(len, RULES.values()))

def mutants(source):
    for name, rules in RULES.items():
        start = source.index("func " + name + "(")
        end = source.find("\nfunc ", start)
        if end == -1:
            end = len(source)
        body = source[start:end]
        for i, (old, new) in enumerate(rules):
            if body.count(old) != 1:
                raise RuntimeError("Mutation anchor changed: " + name + "/" + str(i))
            yield name + "/" + str(i), source[:start] + body.replace(old, new, 1) + source[end:], old, new

def probes():
    # Targeted boundary and authorization checks complement seeded campaigns.
    cases = []
    for op in ["Deposit", "Reserve", "Release", "Settle"]:
        for amount in [-1, 0, 1, 5, 6, 10, 11, 1000000000]:
            for auth, frozen in [(True, False), (False, False), (True, True)]:
                a, h, p = 5, 5, 0
                ok = not frozen and amount > 0 and (op == "Deposit" or auth)
                ok = ok and amount <= (999999990 if op == "Deposit" else 5)
                if ok:
                    if op == "Deposit": a += amount
                    elif op == "Reserve": a -= amount; h += amount
                    elif op == "Release": h -= amount; a += amount
                    else: h -= amount; p += amount
                call = f"{op}({amount}" + ("" if op == "Deposit" else ", " + str(auth).lower()) + ")"
                cases.append({"id": len(cases), "input": {"operation": op, "amount": amount, "authorized": auth, "frozen": frozen},
                              "setup": ["available = 5", "held = 5", "paid = 0", "frozen = false", f"Freeze({str(frozen).lower()})", "ok := " + call],
                              "expression": f"ok == {str(ok).lower()} && Balance() == {a} && Held() == {h} && Paid() == {p}"})
    return cases

def observe(binary, source, cases, env):
    harness = harness_for(cases)
    with tempfile.TemporaryDirectory(prefix="rp-mutant-") as directory:
        path = Path(directory)
        (path / "ledger.gno").write_text(source)
        (path / "ledger_test.gno").write_text(harness)
        (path / "gnomod.toml").write_text('module = "gno.land/r/realmproof/ledger"\n')
        (path / "gno.mod").write_text("module gno.land/r/realmproof/ledger\n")
        result = subprocess.run([binary, "test", "-v", "."], cwd=path, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=12)
    if result.returncode:
        raise RuntimeError("Mutation runtime error: " + diagnostic_excerpt(result.stdout))
    return parse_output(result.stdout, cases)

def run(progress=None):
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI unavailable.")
    source = (Path(__file__).resolve().parent.parent / "realms/ledger/ledger.gno").read_text()
    env = os.environ.copy()
    root = Path.home() / ".gno/source"
    if not env.get("GNOROOT") and (root / "gnovm/stdlibs").is_dir():
        env["GNOROOT"] = str(root)
    cases = probes()
    if not all(observe(binary, source, cases, env)):
        raise RuntimeError("Mutation baseline failed; score invalid.")
    rows = []
    for name, mutant, old, new in mutants(source):
        values = observe(binary, mutant, cases, env)
        witnesses = [c["input"] for c, value in zip(cases, values) if not value]
        expected = {"detected": True}
        observed = {"detected": bool(witnesses)}
        rows.append({"name": name, "expected": expected, "observed": observed,
                     "verdict": evaluate(expected, observed).status,
                     "evidence": {"type": "local_gno", "verified_on_chain": False,
                                  "mutation": {"before": old, "after": new}, "witness_count": len(witnesses),
                                  "witnesses": witnesses[:5], "probe_count": len(cases),
                                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                  "mutant_sha256": hashlib.sha256(mutant.encode()).hexdigest(),
                                  "harness_sha256": hashlib.sha256(harness_for(cases).encode()).hexdigest()}})
        if progress:
            progress(len(rows))
    return rows
