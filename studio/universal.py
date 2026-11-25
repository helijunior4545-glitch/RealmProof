"""Versioned trusted-suite registry. Categories describe intent, not coverage."""
from dataclasses import dataclass
import subprocess
from . import engine, ledger_lab
from .services import evaluate

CATEGORIES = (
    ("unit", "Unit"), ("integration", "Integration"), ("functional", "Functional"),
    ("boundary", "Boundary"), ("negative", "Negative"), ("permission", "Permission"),
    ("state", "State"), ("regression", "Regression"), ("property", "Property-based"),
    ("fuzz", "Fuzz"), ("invariant", "Invariant"), ("security", "Security"),
    ("performance", "Performance"), ("mutation", "Mutation"), ("concurrency", "Concurrency"),
)

@dataclass(frozen=True)
class Suite:
    key: str
    title: str
    categories: tuple
    checks: int
    adapter: object

def transfer():
    rows = []
    for name, family, balance, amount, authorized, status, final in engine.CASES:
        expected = {"status": status, "balance": final, "state_changed": final != balance}
        observed, evidence = engine.execute({"balance": balance, "amount": amount, "authorized": authorized})
        rows.append({"name": name, "expected": expected, "observed": observed,
                     "verdict": evaluate(expected, observed).status, "evidence": evidence})
    return rows

def ledger():
    observed, source, harness, output = ledger_lab.run()
    return [{"name": title, "expected": {"value": expected}, "observed": {"value": observed[key]},
             "verdict": evaluate({"value": expected}, {"value": observed[key]}).status,
             "evidence": {"type": "local_gno", "verified_on_chain": False,
                          "source_sha256": source, "harness_sha256": harness,
                          "output": output if index == 0 else ""}}
            for index, (key, group, title, expression, expected) in enumerate(ledger_lab.CASES)]

SUITES = {
    "transfer-v1": Suite("transfer-v1", "Transfer behavior", ("unit", "functional", "boundary", "negative", "permission", "regression"), len(engine.CASES), transfer),
    "ledger-v1": Suite("ledger-v1", "Ledger lifecycle", ("functional", "state", "boundary", "negative", "permission", "invariant", "regression"), len(ledger_lab.CASES), ledger),
}

def execute(key):
    suite = SUITES[key]
    try:
        rows = suite.adapter()
        if len(rows) != suite.checks:
            raise RuntimeError("Incomplete suite evidence.")
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        return {"suite": key, "execution": "error", "verdict": "inconclusive",
                "rows": [], "reason": str(exc)[-1500:], "verified_on_chain": False}
    return {"suite": key, "execution": "completed",
            "verdict": "passed" if all(r["verdict"] == "passed" for r in rows) else "failed",
            "rows": rows, "verified_on_chain": False}

def catalog():
    return [{"key": key, "title": title,
             "suites": [s.title for s in SUITES.values() if key in s.categories]}
            for key, title in CATEGORIES]
