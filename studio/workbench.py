"""Project-scoped workbench backed by the Studio's existing run records."""

import json
from threading import BoundedSemaphore
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import Project, Scenario, TestRun
from .run_evidence import evidence_document
from .services import parse_json_object, record_evaluation
from .suites import queue_transfer_suite
from .views import WRITE_ROLES, audit, execute_local_scenario, membership_for

run_slots = BoundedSemaphore(2)
limit = 10**12


def project_access(request, slug, project_id, *, write=False):
    member = membership_for(request, slug, write=write)
    item = get_object_or_404(Project, pk=project_id, organization=member.organization)
    return member, item


def get_runs(project):
    return TestRun.objects.filter(
        organization=project.organization, scenario__project=project,
    ).select_related("scenario").order_by("-started_at", "-pk")


def run_data(run, slug):
    commitment = evidence_document(run)
    return {
        "id": str(run.pk), "scenario": str(run.scenario_id), "name": run.scenario.name,
        "status": run.status, "execution": run.execution_status, "started": run.started_at.isoformat(),
        "reason": run.reason if run.status != "error" else "The Gno runner could not complete this run. See the full report.",
        "inputs": run.input_snapshot, "expected": run.expected_snapshot, "observed": run.observed,
        "mismatches": (run.evidence.get("assertions") or {}).get("mismatches", {}),
        "duration": (run.evidence.get("source") or {}).get("duration_ms"),
        "digest": commitment[1] if commitment else None,
        "report": reverse("studio:run_detail", args=[slug, run.pk]),
        "download": reverse("studio:download_run_evidence", args=[slug, run.pk]) if commitment else None,
    }


@login_required
@never_cache
@require_GET
def home(request, slug, project_id):
    member, project = project_access(request, slug, project_id)
    scenarios = list(Scenario.objects.filter(
        organization=member.organization, project=project,
    ).order_by("created_at", "pk"))
    runs = list(get_runs(project)[:30])
    try:
        run_id = UUID(request.GET.get("run", ""))
    except ValueError:
        run_id = None
    if run_id and all(run.pk != run_id for run in runs):
        linked = get_runs(project).filter(pk=run_id).first()
        if linked:
            runs.append(linked)
    workbench = {
        "scenarios": [
            {"id": str(item.pk), "name": item.name, "family": item.get_family_display(),
             "objective": item.objective, "inputs": item.input_data, "expected": item.expected,
             "execute": reverse("studio:workbench_execute", args=[slug, project.pk, item.pk])}
            for item in scenarios
        ],
        "runs": [run_data(run, slug) for run in runs],
        "canWrite": member.role in WRITE_ROLES,
        "history": reverse("studio:workbench_history", args=[slug, project.pk]),
        "suite": reverse("studio:workbench_suite", args=[slug, project.pk]),
        "catalog": reverse("studio:native_catalog", args=[slug]),
        "universal": reverse("studio:universal", args=[slug]),
        "network": reverse("studio:network", args=[slug]),
        "ledger": reverse("studio:ledger_lab", args=[slug]),
        "icons": {name: static(f"studio/phosphor/{name}.svg") for name in (
            "terminal-window", "file-code", "arrow-square-out", "arrow-right", "shield-check",
        )},
        "create": reverse("studio:create_scenario", args=[slug, project.pk]),
    }
    return render(request, "studio/workbench.html", {
        "workbench": workbench, "member": member, "project": project, "scenarios": scenarios, "runs": runs,
    })


@login_required
@never_cache
@require_GET
def history(request, slug, project_id):
    _, project = project_access(request, slug, project_id)
    return JsonResponse({"runs": [run_data(run, slug) for run in get_runs(project)[:30]]})


def transfer_draft(scenario, draft):
    if not isinstance(draft, dict):
        raise ValueError("Provide a valid transfer draft.")
    balance, amount, remaining = (draft.get(key) for key in ("balance", "amount", "remaining"))
    authorized, changed, outcome = (draft.get(key) for key in ("authorized", "changed", "outcome"))
    if (any(type(value) is not int for value in (balance, amount, remaining))
            or not 0 <= balance <= limit or not -limit <= amount <= limit or not 0 <= remaining <= limit
            or type(authorized) is not bool or type(changed) is not bool or outcome not in ("success", "rejected")):
        raise ValueError("Use whole numbers within the transfer limits and set all expectations.")
    return (
        {**scenario.input_data, "balance": balance, "amount": amount, "authorized": authorized},
        {**scenario.expected, "status": outcome, "balance": remaining, "state_changed": changed},
    )


@login_required
@never_cache
@require_POST
def execute(request, slug, project_id, scenario_id):
    member, project = project_access(request, slug, project_id, write=True)
    scenario = get_object_or_404(Scenario, pk=scenario_id, organization=member.organization, project=project)
    payload = request.POST
    if request.content_type == "application/json":
        try:
            payload = parse_json_object(request.body.decode())
        except (UnicodeError, ValueError):
            return JsonResponse({"error": "Invalid test submission."}, status=400)
    if scenario.input_data.get("engine") == "transfer":
        inputs, expected = scenario.input_data, scenario.expected
        if "draft" in payload:
            try:
                inputs, expected = transfer_draft(scenario, payload["draft"])
            except ValueError as exc:
                return JsonResponse({"error": str(exc)}, status=400)
        if not run_slots.acquire(blocking=False):
            return JsonResponse({"error": "The runner is busy. Try again in a moment."}, status=429)
        try:
            run = execute_local_scenario(member, request.user, scenario, inputs, expected)
        finally:
            run_slots.release()
    else:
        observed = payload.get("observed")
        if not isinstance(observed, dict):
            return JsonResponse({"error": "Observed evidence must be a JSON object."}, status=400)
        with transaction.atomic():
            run = TestRun.objects.create(
                scenario=scenario, organization=member.organization, initiated_by=request.user,
                input_snapshot=scenario.input_data, expected_snapshot=scenario.expected,
            )
            record_evaluation(run, observed, execution_status="external_evidence",
                              evidence={"type": "user_supplied", "verified_on_chain": False})
            audit(member.organization, request.user, "run.evaluated", run.pk)
    return JsonResponse({"run": run_data(run, slug)}, status=201)


@login_required
@never_cache
@require_POST
def suite(request, slug, project_id):
    member, project = project_access(request, slug, project_id, write=True)
    count = queue_transfer_suite(member, request.user, project)
    return JsonResponse({"queued": count, "runs": [run_data(run, slug) for run in get_runs(project)[:30]]})
