"""Bounded, non-executing source inventory."""
import hashlib
import json
import re
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Project, Membership, SourceSnapshot

MAX_FILES = 100
MAX_BYTES = 1024 * 1024

def inventory(files):
    if not isinstance(files, dict) or not 1 <= len(files) <= MAX_FILES:
        raise ValidationError("Invalid file count.")
    result = {}
    total = 0
    for path, source in files.items():
        if not isinstance(path, str) or len(path) > 240 or not path.endswith(".gno") or any(not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", part) for part in path.split("/")):
            raise ValidationError("Invalid source path.")
        if not isinstance(source, str) or "\x00" in source:
            raise ValidationError("Invalid source text.")
        try:
            data = source.encode("utf-8")
        except UnicodeError as exc:
            raise ValidationError("Invalid UTF-8 source.") from exc
        total += len(data)
        if total > MAX_BYTES:
            raise ValidationError("Source size limit exceeded.")
        result[path] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "source": source}
    manifest = {p: f["sha256"] for p, f in result.items()}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return digest, result

@transaction.atomic
def capture(member, project_id, files):
    from django.core.exceptions import PermissionDenied
    if not Membership.objects.filter(pk=member.pk, organization_id=member.organization_id, user_id=member.user_id, role__in=["owner", "admin", "editor"]).exists():
        raise PermissionDenied
    project = Project.objects.select_for_update().get(pk=project_id, organization_id=member.organization_id)
    digest, records = inventory(files)
    existing = SourceSnapshot.objects.filter(project=project, digest=digest).first()
    if existing:
        return existing, False
    if SourceSnapshot.objects.filter(project=project).count() >= 20:
        raise ValidationError("Snapshot quota exceeded.")
    return SourceSnapshot.objects.create(project=project, digest=digest, files=records), True

def compare(before, after):
    if before.project_id != after.project_id:
        raise ValidationError("Snapshots must belong to the same project.")
    a, b = before.files, after.files
    return {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()), "modified": sorted(p for p in a.keys() & b.keys() if a[p]["sha256"] != b[p]["sha256"])}
