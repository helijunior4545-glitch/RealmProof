"""Deterministic diagnostic hints; never infer a passing assertion."""
def classify(result):
    if result.get("execution") == "completed":
        return "assertion_mismatch" if result.get("verdict") == "failed" else "none"
    reason = result.get("reason", "").lower()
    for fragment, category in (
        ("immutable post-init", "immutable_package"),
        ("timed out", "timeout"),
        ("unavailable", "runtime_unavailable"),
        ("build error", "runtime_build_or_test_error"),
        ("incomplete", "incomplete_evidence"),
        ("lease expired", "worker_interrupted"),
        ("permission denied", "permission_error"),
    ):
        if fragment in reason:
            return category
    return "unknown_execution_error"
