"""Tenant-first studio views. All writes require membership checks."""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from .forms import ProjectForm, ScenarioForm
from .models import AuditEvent, Membership, Organization, Project, Scenario, TestRun
from .services import parse_json_object, record_evaluation

WRITE_ROLES = ("owner", "admin", "editor")


def membership_for(request, slug, write=False):
    member = get_object_or_404(
        Membership.objects.select_related("organization"),
        organization__slug=slug,
        user=request.user,
    )
    if write and member.role not in WRITE_ROLES:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to modify this workspace.")
    return member


def audit(org, actor, action, target):
    AuditEvent.objects.create(organization=org, actor=actor, action=action, target=str(target))


@login_required
def dashboard(request):
    memberships = Membership.objects.filter(user=request.user).select_related("organization").order_by("organization__name")
    return render(request, "studio/dashboard.html", {"memberships": memberships})


@login_required
@require_POST
def create_organization(request):
    name, slug = request.POST.get("name", "").strip(), request.POST.get("slug", "").strip().lower()
    from django.core.validators import validate_slug
    try:
        validate_slug(slug)
        if not name or len(name) > 120 or len(slug) > 50 or not slug:
            raise ValidationError("A valid organization name and slug are required.")
        with transaction.atomic():
            org = Organization.objects.create(name=name, slug=slug)
            Membership.objects.create(user=request.user, organization=org, role="owner")
            audit(org, request.user, "organization.created", org.pk)
    except (ValidationError, ValueError) as exc:
        messages.error(request, f"Unable to create workspace: {exc}")
        return redirect("studio:dashboard")
    except Exception as exc:
        from django.db import IntegrityError
        if not isinstance(exc, IntegrityError):
            raise
        messages.error(request, "Workspace slug is already in use.")
        return redirect("studio:dashboard")
    return redirect("studio:organization", slug=org.slug)


@login_required
def organization(request, slug):
    member = membership_for(request, slug)
    projects = Project.objects.filter(organization=member.organization).order_by("-created_at")
    return render(request, "studio/organization.html", {"member": member, "projects": projects})


@login_required
def create_project(request, slug):
    member = membership_for(request, slug, write=True)
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.organization = member.organization
            project.save()
            audit(member.organization, request.user, "project.created", project.pk)
            return redirect("studio:project", slug=slug, project_id=project.pk)
    else:
        form = ProjectForm()
    return render(request, "studio/form.html", {"form": form, "heading": "New project", "member": member})


@login_required
def project(request, slug, project_id):
    member = membership_for(request, slug)
    item = get_object_or_404(Project, pk=project_id, organization=member.organization)
    scenarios = Scenario.objects.filter(project=item, organization=member.organization).order_by("-created_at")
    return render(request, "studio/project.html", {"member": member, "project": item, "scenarios": scenarios})


@login_required
def create_scenario(request, slug, project_id):
    member = membership_for(request, slug, write=True)
    item = get_object_or_404(Project, pk=project_id, organization=member.organization)
    if request.method == "POST":
        form = ScenarioForm(request.POST)
        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.organization = member.organization
            scenario.project = item
            try:
                scenario.save()
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                audit(member.organization, request.user, "scenario.created", scenario.pk)
                return redirect("studio:project", slug=slug, project_id=project_id)
    else:
        form = ScenarioForm(initial={"input_data": {}, "expected": {"status": "ok"}})
    return render(request, "studio/form.html", {"form": form, "heading": "New test scenario", "member": member})


@login_required
@require_POST
def start_run(request, slug, scenario_id):
    member = membership_for(request, slug, write=True)
    scenario = get_object_or_404(Scenario, pk=scenario_id, organization=member.organization)
    run = TestRun.objects.create(
        scenario=scenario, organization=member.organization, initiated_by=request.user,
        input_snapshot=scenario.input_data, expected_snapshot=scenario.expected,
        status="pending", execution_status="not_executed",
        reason="Awaiting independently collected evidence. No blockchain transaction was submitted.",
    )
    audit(member.organization, request.user, "run.created", run.pk)
    return redirect("studio:run_detail", slug=slug, run_id=run.pk)


@login_required
def run_detail(request, slug, run_id):
    member = membership_for(request, slug)
    run = get_object_or_404(TestRun.objects.select_related("scenario"), pk=run_id, organization=member.organization)
    return render(request, "studio/run.html", {
        "member": member, "run": run,
        "expected_pretty": json.dumps(run.expected_snapshot, indent=2),
        "observed_pretty": json.dumps(run.observed, indent=2),
        "evidence_pretty": json.dumps(run.evidence, indent=2),
    })


@login_required
@require_POST
def evaluate_run(request, slug, run_id):
    member = membership_for(request, slug, write=True)
    with transaction.atomic():
        run = get_object_or_404(TestRun.objects.select_for_update(), pk=run_id, organization=member.organization)
        if run.status != "pending":
            messages.error(request, "This run is immutable after evaluation.")
            return redirect("studio:run_detail", slug=slug, run_id=run.pk)
        try:
            observed = parse_json_object(request.POST.get("observed", ""))
        except (ValueError, json.JSONDecodeError) as exc:
            messages.error(request, f"Invalid evidence: {exc}")
            return redirect("studio:run_detail", slug=slug, run_id=run.pk)
        record_evaluation(
            run, observed, execution_status="external_evidence",
            evidence={"type": "user_supplied", "verified_on_chain": False},
        )
        audit(member.organization, request.user, "run.evaluated", run.pk)
    return redirect("studio:run_detail", slug=slug, run_id=run.pk)


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unhealthy"}, status=503)
    return JsonResponse({"status": "ok"})
