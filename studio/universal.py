"""Versioned trusted-suite registry. Categories describe intent, not coverage."""
from dataclasses import dataclass
import subprocess
from . import engine, ledger_lab, specialized, mutation, security_campaign, regression
from functools import partial
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

def transfer(progress=None):
    rows = []
    for name, family, balance, amount, authorized, status, final in engine.CASES:
        expected = {"status": status, "balance": final, "state_changed": final != balance}
        observed, evidence = engine.execute({"balance": balance, "amount": amount, "authorized": authorized})
        rows.append({"name": name, "expected": expected, "observed": observed,
                     "verdict": evaluate(expected, observed).status, "evidence": evidence})
        if progress:
            progress(len(rows))
    return rows

def ledger(progress=None):
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

for kind, (count, seed) in specialized.SPECS.items():
    SUITES[kind + "-v1"] = Suite(kind + "-v1", kind.title() + " campaign", (kind,), count, partial(specialized.run, kind))

SUITES["mutation-v1"] = Suite("mutation-v1", "Mutation detection", ("mutation",), mutation.COUNT, mutation.run)

SUITES["security-v1"] = Suite("security-v1", "Adversarial security campaign", ("security",), security_campaign.COUNT, security_campaign.run)

SUITES["regression-v1"] = Suite("regression-v1", "Historical behavior comparison", ("regression",), regression.COUNT, regression.run)

def execute(key, progress=None):
    suite = SUITES[key]
    try:
        rows = suite.adapter(progress)
        if progress and len(rows) == suite.checks:
            progress(len(rows))
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
