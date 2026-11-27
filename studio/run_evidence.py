"""Encode completed Gno runs for an independently reproducible digest."""

import hashlib
import json


def evidence_document(run):
    if run.execution_status != "local_gno" or run.status not in {"passed", "failed", "inconclusive"}:
        return None
    source = run.evidence.get("source") or {}
    if not source.get("source_sha256") or not source.get("harness_sha256"):
        return None

    report = {
        "schema": "realmproof.evidence.v1",
        "run_id": str(run.pk),
        "inputs": run.input_snapshot,
        "expected": run.expected_snapshot,
        "observed": run.observed,
        "verdict": run.status,
        "source": {
            "type": "local_gno",
            "source_sha256": source["source_sha256"],
            "harness_sha256": source["harness_sha256"],
        },
    }
    payload = json.dumps(
        report, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return payload, hashlib.sha256(payload).hexdigest()
