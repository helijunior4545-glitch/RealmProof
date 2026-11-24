"""Signed, expiring review links. No anonymous execution or tenant data mutation."""
import json
import secrets
import hashlib
from django.core import signing
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from .models import Project, TestRun, AuditEvent
from .views import membership_for

SALT = "realmproof.review.v1"
MAX_AGE = 86400

@login_required
@require_POST
def publish(request, slug, project_id):
    member = membership_for(request, slug, write=True)
    project = get_object_or_404(Project, pk=project_id, organization=member.organization)
    runs = TestRun.objects.filter(organization=member.organization, scenario__project=project,
        execution_status="local_gno", status__in=["passed","failed","inconclusive"]).select_related("scenario").order_by("-started_at")[:30]
    snapshot = [{"name": run.scenario.name, "objective": run.scenario.objective,
        "expected": run.expected_snapshot, "observed": run.observed, "verdict": run.status,
        "reason": run.reason} for run in runs]
    nonce = secrets.token_urlsafe(24)
    event = AuditEvent.objects.create(organization=member.organization, actor=request.user,
        action="review.published", target=str(project.pk),
        details={"nonce_hash": hashlib.sha256(nonce.encode()).hexdigest(), "title": project.name, "runs": snapshot})
    token = signing.dumps({"id": str(event.pk), "nonce": nonce}, salt=SALT)
    response = render(request, "studio/review_publish.html", {"member": member, "project": project,
        "link": request.build_absolute_uri(reverse("studio:open_review", args=[token])), "count": len(snapshot)})
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response

@require_GET
def open_review(request, token):
    try:
        payload = signing.loads(token, salt=SALT, max_age=MAX_AGE)
        event = AuditEvent.objects.get(pk=payload["id"], action="review.published")
        if not secrets.compare_digest(event.details["nonce_hash"], hashlib.sha256(payload["nonce"].encode()).hexdigest()):
            raise Http404
    except (signing.BadSignature, AuditEvent.DoesNotExist, KeyError, ValueError):
        raise Http404("Review expired or unavailable.")
    runs = []
    for run in event.details["runs"]:
        runs.append(dict(run, expected_text=json.dumps(run["expected"], indent=2), observed_text=json.dumps(run["observed"], indent=2)))
    response = render(request, "studio/review_public.html", {"title": event.details["title"], "runs": runs})
    response["Cache-Control"] = "no-store, private"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
