"""Deterministic adversarial sequences against the trusted ledger fixture."""
import random
from .specialized import run as run_cases, literal

SEED = 4201
GROUPS = {"authorization": 120, "replay": 90, "state": 120,
          "financial": 120, "boundary": 90, "freeze": 60}
COUNT = sum(GROUPS.values())
CAP = 1000000000

def campaign():
    rng = random.Random(SEED)
    cases = []
    for group, count in GROUPS.items():
        for i in range(count):
            funds = rng.randint(1, 1000000)
            n = rng.randint(1, funds)
            op = rng.choice(["Reserve", "Release", "Settle"])
            if group == "authorization":
                ops = [("Reserve", n, True), (op, n, False)]
            elif group == "replay":
                ops = [("Reserve", n, True), ("Settle", n, True), ("Settle", n, True)]
            elif group == "state":
                ops = [(rng.choice(["Reserve", "Release", "Settle", "Deposit"]),
                        rng.randint(-1, funds+1), rng.choice([True, False])) for _ in range(8)]
            elif group == "financial":
                ops = [("Reserve", n, True), ("Release", n//2, True),
                       ("Settle", n-n//2, True), ("Deposit", CAP-funds, True), ("Deposit", 1, True)]
            elif group == "boundary":
                funds = rng.choice([1, CAP-1, CAP, rng.randint(1, CAP)])
                ops = [(rng.choice(["Deposit", "Reserve", "Release", "Settle"]),
                        rng.choice([-CAP, -1, 0, 1, funds, funds+1, CAP, CAP+1]), True) for _ in range(6)]
            else:
                ops = [("Reserve", n, True), ("Freeze", True, True),
                       ("Deposit", n, True), ("Reserve", n, True),
                       ("Release", n, True), ("Settle", n, True),
                       ("Freeze", False, True), ("Release", n, True)]
            a, h, p, frozen = funds, 0, 0, False
            setup = ["available = 0", "held = 0", "paid = 0", "frozen = false",
                     f"initial := Deposit({funds})", f"valid := initial && Balance() == {funds} && Held() == 0 && Paid() == 0"]
            for j, (operation, amount, auth) in enumerate(ops):
                if operation == "Freeze":
                    frozen = amount
                    ok = True
                    call = f"Freeze({literal(amount)})"
                elif operation == "Deposit":
                    ok = not frozen and 0 < amount <= CAP-a-h-p
                    if ok: a += amount
                    call = f"Deposit({amount})"
                else:
                    ok = not frozen and auth and 0 < amount <= (a if operation == "Reserve" else h)
                    if ok:
                        if operation == "Reserve": a -= amount; h += amount
                        elif operation == "Release": h -= amount; a += amount
                        else: h -= amount; p += amount
                    call = f"{operation}({amount}, {literal(auth)})"
                setup += [f"step{j} := {call}",
                          f"valid = (step{j} == {literal(ok)} && Balance() == {a} && Held() == {h} && Paid() == {p}) && valid"]
            cases.append({"id": len(cases), "input": {"category": group, "funds": funds, "operations": ops},
                          "setup": setup, "expression": "valid", "expected": True})
    return cases

def run(progress=None):
    return run_cases("security", progress, cases=campaign(), seed=SEED)
