"""Evaluate ordered Onyx transaction receipts as a single experiment."""
from time import monotonic

from . import chain

MAX_STEPS = 6


def validate_steps(value):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_STEPS:
        raise ValueError(f"Provide between 1 and {MAX_STEPS} steps.")
    steps = []
    hashes = set()
    for number, step in enumerate(value, 1):
        if not isinstance(step, dict):
            raise ValueError(f"Step {number} is invalid.")
        name, actor, digest, height, expected = (
            step.get(key) for key in ("name", "actor", "hash", "height", "expected")
        )
        if not all(isinstance(item, str) and 0 < len(item.strip()) <= 96 for item in (name, actor, digest)):
            raise ValueError(f"Step {number} needs a name, actor label and transaction hash.")
        if type(height) is not int or not 1 <= height < 10**18 or expected not in ("passed", "failed"):
            raise ValueError(f"Step {number} needs a block height and expected execution outcome.")
        try:
            digest = chain.normalize_hash(digest.strip()).hex()
        except chain.ChainError as exc:
            raise ValueError(f"Step {number}. {exc}") from exc
        if digest in hashes:
            raise ValueError(f"Step {number} reuses a transaction from another step.")
        hashes.add(digest)
        steps.append({"name": name.strip(), "actor": actor.strip(), "hash": digest, "height": height, "expected": expected})
    return steps


def evaluate(steps):
    # Stop scheduling new requests when the interactive budget is exhausted.
    deadline = monotonic() + 18
    observed_steps = []
    previous = None
    for step in steps:
        result = {**step, "actor_verification": "declared"}
        try:
            if monotonic() >= deadline:
                raise chain.ChainError("Verification time budget reached.")
            receipt = chain.transaction("testnet", step["hash"], step["height"])
        except chain.ChainError as exc:
            result.update(verdict="inconclusive", reason=str(exc))
        else:
            position = receipt["height"], receipt["index"]
            ordered = previous is None or previous < position
            actual = receipt["execution"]
            verdict = "failed" if not ordered else "inconclusive" if actual == "unknown" else (
                "passed" if actual == step["expected"] else "failed"
            )
            result.update(verdict=verdict, observed=actual, ordered=ordered, receipt=receipt)
            previous = max(previous or position, position)
        observed_steps.append(result)
    verdicts = {step["verdict"] for step in observed_steps}
    return {
        "schema": "realmproof.network-experiment.v1", "chain_id": chain.NETWORKS["testnet"][0],
        "verdict": "failed" if "failed" in verdicts else "inconclusive" if "inconclusive" in verdicts else "passed",
        "steps": observed_steps,
    }
