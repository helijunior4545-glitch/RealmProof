"""Deterministic, non-signing assertions. No mocked chain transactions."""
import json


def equal_json(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal_json(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal_json(x, y) for x, y in zip(a, b))
    return a == b

from dataclasses import dataclass
from django.utils import timezone


@dataclass(frozen=True)
class AssertionResult:
    status: str
    reason: str
    evidence: dict


def evaluate(expected, observed):
    """Compare explicit expected fields only; no synthetic chain evidence."""
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        return AssertionResult("inconclusive", "Evidence must be JSON objects.", {})
    if not expected:
        return AssertionResult("inconclusive", "No assertions have been defined.", {})
    mismatches = {key: {"expected": value, "actual": observed.get(key), "present": key in observed}
                  for key, value in expected.items() if key not in observed or not equal_json(observed[key], value)}
    return AssertionResult(
        "failed" if mismatches else "passed",
        "Observed values differ from the expected assertions." if mismatches else "All expected fields match the supplied evidence.",
        {"compared_fields": sorted(expected), "mismatches": mismatches},
    )


def record_evaluation(run, observed, *, execution_status, evidence=None):
    """Persist an evaluation. Must be called after observed evidence exists."""
    result = evaluate(run.expected_snapshot, observed)
    run.observed = observed
    run.status = result.status
    run.execution_status = execution_status
    run.reason = result.reason
    run.evidence = {"assertions": result.evidence, "source": evidence or {}}
    run.finished_at = timezone.now()
    run.save(update_fields=["observed", "status", "execution_status", "reason", "evidence", "finished_at"])
    return result


def parse_json_object(text):
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value
