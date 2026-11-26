import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .models import Project, SourceSnapshot
from .views import membership_for
from .source_discovery import capture, compare
from .structural import analyze

def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate path.")
        result[key] = value
    return result

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def overview(request, slug, project_id):
    member = membership_for(request, slug, write=request.method == "POST")
    project = get_object_or_404(Project, pk=project_id, organization=member.organization)
    error = ""
    if request.method == "POST":
        try:
            raw = request.POST.get("manifest", "")
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("Manifest too large.")
            snapshot, _ = capture(member, project.pk, json.loads(raw, object_pairs_hook=unique_pairs))
            return redirect(request.path + "?snapshot=" + str(snapshot.pk))
        except (ValueError, ValidationError, RecursionError):
            error = "Invalid manifest or snapshot quota exceeded."
    snapshots = project.source_snapshots.order_by("-created_at", "-pk")
    selected = snapshots.first()
    if request.GET.get("snapshot"):
        from uuid import UUID
        try:
            key = UUID(request.GET["snapshot"])
        except ValueError:
            from django.http import Http404
            raise Http404
        selected = get_object_or_404(snapshots, pk=key)
    previous = snapshots.filter(created_at__lt=selected.created_at).first() if selected else None
    path = request.GET.get("file", "")
    record = selected.files.get(path) if selected else None
    return render(request, "studio/source_discovery.html", {"member": member, "project": project, "snapshots": snapshots.defer("files"), "selected": selected, "changes": compare(previous, selected) if previous else None, "record": record, "structure": analyze(record["source"]) if record else None, "path": path, "record_path": path, "error": error}, status=400 if error else 200)
