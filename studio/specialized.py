"""Bounded, reproducible Gno fixture campaigns; no tenant-supplied code."""
import hashlib
import os
import random
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from .ledger_lab import diagnostic_excerpt
from .services import evaluate

SPECS = {"integration": (30, 3101), "property": (100, 3102),
         "fuzz": (500, 3103), "invariant": (100, 3104)}

def literal(value):
    return str(value).lower() if isinstance(value, bool) else str(value)

def campaign(kind):
    count, seed = SPECS[kind]
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        funds = rng.randint(1, 1000000)
        amount = rng.randint(1, funds)
        setup = ["available = 0", "held = 0", "paid = 0", "frozen = false", f"Deposit({funds})"]
        inputs = {"funds": funds, "amount": amount}
        if kind == "integration":
            release = rng.randint(0, amount-1)
            inputs["release"] = release
            setup += [f"Reserve({amount}, true)"]
            if release:
                setup += [f"Release({release}, true)"]
            setup += [f"Settle({amount-release}, true)"]
            expression = f"Balance() == {funds-amount+release} && Held() == 0 && Paid() == {amount-release}"
            expected = True
        elif kind == "property":
            setup += [f"Reserve({amount}, true)", f"Release({amount}, true)"]
            expression = f"Balance() == {funds} && Held() == 0 && Paid() == 0"
            expected = True
        elif kind == "fuzz":
            amount = rng.choice([-1000000001, -1, 0, 1, funds, funds+1, 1000000001, rng.randint(-funds, funds*2)])
            authorized = rng.choice([True, False])
            frozen = rng.choice([True, False])
            operation = rng.choice(["Deposit", "Reserve", "Release", "Settle"])
            initial_held = funds//2
            setup += [f"Reserve({initial_held}, true)", f"Freeze({literal(frozen)})"]
            a, h, p = funds-initial_held, initial_held, 0
            ok = not frozen and amount > 0 and (operation == "Deposit" or authorized)
            if operation == "Deposit":
                ok = ok and amount <= 1000000000-funds
                if ok: a += amount
                call = f"Deposit({amount})"
            else:
                ok = ok and amount <= (a if operation == "Reserve" else h)
                if ok:
                    if operation == "Reserve": a -= amount; h += amount
                    elif operation == "Release": h -= amount; a += amount
                    else: h -= amount; p += amount
                call = f"{operation}({amount}, {literal(authorized)})"
            inputs.update(amount=amount, authorized=authorized, frozen=frozen, operation=operation, initial_held=initial_held)
            setup += [f"ok := {call}"]
            expression = f"ok == {literal(ok)} && Balance() == {a} && Held() == {h} && Paid() == {p}"
            expected = True
        else:
            operations = []
            for _ in range(8):
                op = rng.choice(["Reserve", "Release", "Settle"])
                n = rng.randint(-1, funds+1)
                auth = rng.choice([True, False])
                operations.append({"operation": op, "amount": n, "authorized": auth})
                setup.append(f"{op}({n}, {literal(auth)})")
            inputs["operations"] = operations
            expression = f"Balance() >= 0 && Held() >= 0 && Paid() >= 0 && Balance()+Held()+Paid() == {funds}"
            expected = True
        cases.append({"id": i, "input": inputs, "setup": setup, "expression": expression, "expected": expected})
    return cases

def harness_for(cases):
    lines = ['package ledger', 'import "testing"', 'import "fmt"', 'func TestCampaign(t *testing.T) {']
    for case in cases:
        lines += ["{", *case["setup"], 'fmt.Println("RP_CASE %d", %s)' % (case["id"], case["expression"]), "}"]
    return "\n".join(lines + ["}", ""])

def parse_output(output, cases):
    matches = re.findall(r"(?m)^\s*RP_CASE ([0-9]+) (true|false)\s*$", output)
    if [int(key) for key, _ in matches] != [c["id"] for c in cases]:
        raise RuntimeError("Incomplete campaign evidence: " + diagnostic_excerpt(output))
    return [value == "true" for _, value in matches]

def run(kind, progress=None):
    binary = shutil.which(os.environ.get("REALMPROOF_GNO_BINARY", "gno"))
    if not binary:
        raise RuntimeError("Gno CLI unavailable.")
    source = (Path(__file__).resolve().parent.parent / "realms/ledger/ledger.gno").read_text()
    cases = campaign(kind)
    env = os.environ.copy()
    root = Path.home() / ".gno/source"
    if not env.get("GNOROOT") and (root / "gnovm/stdlibs").is_dir():
        env["GNOROOT"] = str(root)
    rows = []
    for offset in range(0, len(cases), 50):
        batch = cases[offset:offset+50]
        harness = harness_for(batch)
        with tempfile.TemporaryDirectory(prefix="rp-campaign-") as directory:
            path = Path(directory)
            (path / "ledger.gno").write_text(source)
            (path / "ledger_test.gno").write_text(harness)
            (path / "gnomod.toml").write_text('module = "gno.land/r/realmproof/ledger"\n')
            (path / "gno.mod").write_text("module gno.land/r/realmproof/ledger\n")
            result = subprocess.run([binary, "test", "-v", "."], cwd=path, env=env, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError("Gno campaign execution error: " + diagnostic_excerpt(result.stdout))
        values = parse_output(result.stdout, batch)
        for case, value in zip(batch, values):
            expected = {"predicate": case["expected"]}
            observed = {"predicate": value}
            rows.append({"name": f"{kind} / {case['id']}", "expected": expected, "observed": observed,
                         "verdict": evaluate(expected, observed).status,
                         "evidence": {"type": "local_gno", "verified_on_chain": False, "seed": SPECS[kind][1],
                                      "case_id": case["id"], "input": case["input"], "predicate": case["expression"],
                                      "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                      "harness_sha256": hashlib.sha256(harness.encode()).hexdigest()}})
        if progress:
            progress(len(rows))
    return rows
