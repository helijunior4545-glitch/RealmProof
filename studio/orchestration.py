"""Persist explicitly confirmed intent; never execute imported source."""
import hashlib
import json
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import Membership, Project, SourceSnapshot, SourceTestDraft, AuditEvent
from .structural import analyze

def proposal_key(proposal):
    return hashlib.sha256(json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

@transaction.atomic
def confirm(member, project_id, snapshot_id, path, key, expected):
    if not Membership.objects.select_for_update().filter(pk=member.pk, user_id=member.user_id, organization_id=member.organization_id, role__in=["owner", "admin", "editor"]).exists():
        raise PermissionDenied
    if not isinstance(expected, dict) or not expected or len(json.dumps(expected, allow_nan=False).encode()) > 8192:
        raise ValidationError("Expected outcome must be a nonempty bounded JSON object.")
    project = Project.objects.select_for_update().get(pk=project_id, organization_id=member.organization_id)
    snapshot = SourceSnapshot.objects.get(pk=snapshot_id, project=project)
    record = snapshot.files.get(path)
    if not record or hashlib.sha256(record["source"].encode()).hexdigest() != record["sha256"]:
        raise ValidationError("Source unavailable or changed.")
    proposals = analyze(record["source"]).get("recommendations", {}).get("items", [])
    proposal = next((p for p in proposals if proposal_key(p) == key), None)
    if proposal is None:
        raise ValidationError("Proposal unavailable.")
    existing = SourceTestDraft.objects.filter(snapshot=snapshot, path=path, proposal_key=key).first()
    if existing:
        if json.dumps(existing.expected, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise ValidationError("A draft already exists with different intent.")
        return existing
    if SourceTestDraft.objects.filter(snapshot__project=project).count() >= 500:
        raise ValidationError("Draft quota exceeded.")
    draft = SourceTestDraft.objects.create(snapshot=snapshot, path=path, source_digest=record["sha256"], proposal_key=key, proposal=proposal, expected=expected, created_by_id=member.user_id)
    AuditEvent.objects.create(organization_id=member.organization_id, actor_id=member.user_id, action="source_draft_confirmed", target=str(draft.pk))
    return draft
