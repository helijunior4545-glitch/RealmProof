"""Fail-closed execution preflight; no imported code execution."""
import hashlib
import json
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import Membership, SourceTestDraft
from .orchestration import proposal_key

@transaction.atomic
def prepare(member, draft_id):
    if not Membership.objects.select_for_update().filter(
        pk=member.pk, user_id=member.user_id,
        organization_id=member.organization_id,
        role__in=["owner", "admin", "editor"],
    ).exists():
        raise PermissionDenied
    draft = SourceTestDraft.objects.select_related("snapshot__project").get(
        pk=draft_id, snapshot__project__organization_id=member.organization_id)
    record = draft.snapshot.files.get(draft.path)
    if not isinstance(record, dict) or not isinstance(record.get("source"), str):
        raise ValidationError("Source unavailable.")
    digest = hashlib.sha256(record["source"].encode("utf-8")).hexdigest()
    if digest != draft.source_digest or digest != record.get("sha256"):
        raise ValidationError("Source integrity mismatch.")
    if proposal_key(draft.proposal) != draft.proposal_key:
        raise ValidationError("Proposal integrity mismatch.")
    if not isinstance(draft.expected, dict) or not draft.expected:
        raise ValidationError("Expected assertions unavailable.")
    try:
        encoded = json.dumps(draft.expected, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValidationError("Invalid expected assertions.") from exc
    if len(encoded) > 8192:
        raise ValidationError("Expected assertions exceed limit.")
    return {
        "draft_id": str(draft.pk), "snapshot_id": str(draft.snapshot_id),
        "path": draft.path, "source_digest": digest,
        "proposal_key": draft.proposal_key,
        "expected_digest": hashlib.sha256(encoded).hexdigest(),
        "execution": "not_executed", "verdict": "inconclusive",
        "blockers": ["isolated_runtime_not_available", "executable_harness_not_confirmed"],
        "verified_on_chain": False,
    }
