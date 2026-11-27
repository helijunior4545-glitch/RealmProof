"""Bounded regression queue and tenant-scoped evidence export."""
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from .models import Organization, Project, Scenario, TestRun
from .views import membership_for, audit

@login_required
@require_POST
def queue_suite(request, slug, project_id):
    member = membership_for(request, slug, write=True)
    project = get_object_or_404(Project, pk=project_id, organization=member.organization)
    queue_transfer_suite(member, request.user, project)
    return redirect("studio:project", slug=slug, project_id=project.pk)


def queue_transfer_suite(member, user, project):
    with transaction.atomic():
        Organization.objects.select_for_update().get(pk=member.organization_id)
        pending = TestRun.objects.filter(organization=member.organization, execution_status__in=["queued","local_running"], status="pending").count()
        scenarios = list(Scenario.objects.filter(organization=member.organization, project=project, input_data__engine="transfer").order_by("pk")[:max(0, min(20, 20-pending))])
        for scenario in scenarios:
            TestRun.objects.create(organization=member.organization, scenario=scenario, initiated_by=user,
                input_snapshot=scenario.input_data, expected_snapshot=scenario.expected, execution_status="queued", reason="Waiting for local execution worker.")
        audit(member.organization, user, "suite.queued", project.pk)
    return len(scenarios)

@login_required
@require_GET
def export_project(request, slug, project_id):
    member = membership_for(request, slug)
    project = get_object_or_404(Project, pk=project_id, organization=member.organization)
    runs = TestRun.objects.filter(organization=member.organization, scenario__project=project).order_by("-started_at")[:200]
    response = JsonResponse({"project": str(project.pk), "runs": [{"id":str(r.pk), "status":r.status,"execution_status":r.execution_status,"expected":r.expected_snapshot,"observed":r.observed,"evidence":r.evidence} for r in runs]})
    response["Content-Disposition"] = 'attachment; filename="realmproof-evidence.json"'
    response["Cache-Control"] = "no-store"
    return response
