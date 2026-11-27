"""Public demo entry with server-side credentials and fail-closed authorization."""
import logging
import os
from subprocess import TimeoutExpired
from threading import BoundedSemaphore

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from . import engine
from .models import Membership, Project
from .services import evaluate
from .views import membership_for

logger = logging.getLogger(__name__)
preview_slots = BoundedSemaphore(2)
preview_cases = [
    {"id": slug, "name": name, "inputs": {"balance": balance, "amount": amount, "authorized": authorized},
     "expected": {"status": status, "balance": final, "state_changed": final != balance}}
    for slug, (name, _, balance, amount, authorized, status, final) in zip(
        ("valid", "insufficient", "permission", "exact"), engine.CASES
    )
]

def studio_destination(request, route="studio:project"):
    if not request.user.is_authenticated:
        return None
    for slug in Membership.objects.filter(user=request.user).order_by("organization__slug").values_list("organization__slug", flat=True):
        try:
            member = membership_for(request, slug)
        except Http404:
            continue
        project = Project.objects.filter(organization=member.organization).order_by("-created_at", "pk").first()
        if project:
            return reverse(route, kwargs={"slug": slug, "project_id": project.pk})
    return None

def render_landing(request, case=None, result=None, error=None, status=200):
    return render(request, "studio/guest_entry.html", {
        "studio_url": studio_destination(request, "studio:workbench"),
        "dashboard_url": reverse("studio:dashboard"),
        "isolated_guest": os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1",
        "preview_cases": preview_cases,
        "selected_case": case or preview_cases[1],
        "preview_result": result,
        "preview_error": error,
    }, status=status)


@never_cache
@require_GET
def entry(request):
    return render_landing(request)

@never_cache
@require_POST
def start(request):
    route = "studio:workbench" if request.POST.get("destination") == "workbench" else "studio:project"
    if request.user.is_authenticated:
        return redirect(studio_destination(request, route) or "studio:dashboard")
    username = os.getenv("REALMPROOF_DEMO_USERNAME", "")
    password = os.getenv("REALMPROOF_DEMO_PASSWORD", "")
    user = authenticate(request, username=username, password=password) if username == "hackathon_demo_public" and password else None
    if user and user.is_active and not user.is_staff and not user.is_superuser:
        memberships = list(Membership.objects.filter(user=user).select_related("organization")[:2])
        if len(memberships) == 1 and memberships[0].organization.slug.startswith("review-") and memberships[0].role == "editor":
            if os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1":
                from .guest_provisioning import provision
                result = provision(user)
                if result is None:
                    messages.error(request, "Guest capacity reached. Please try again later.")
                    return redirect("studio:public_demo")
                visitor, org, project = result
                login(request, visitor, backend="django.contrib.auth.backends.ModelBackend")
                request.session.set_expiry(3600)
                request.session["realmproof_guest"] = True
                return redirect(route, slug=org.slug, project_id=project.pk)
            login(request, user)
            request.session.set_expiry(3600)
            request.session['realmproof_guest'] = True
            project = Project.objects.filter(organization=memberships[0].organization, name="Transfer verification lab").order_by("created_at").first()
            if project:
                return redirect(route, slug=memberships[0].organization.slug, project_id=project.pk)
            return redirect("studio:organization", slug=memberships[0].organization.slug)
    logger.warning("Demo launch rejected: configured=%s authenticated=%s", bool(username and password), bool(user))
    messages.error(request, "Demo access is temporarily unavailable. Please try again later.")
    return redirect("studio:public_demo")


@never_cache
@require_POST
def preview(request):
    case = next((item for item in preview_cases if item["id"] == request.POST.get("scenario")), None)

    def respond(data, status=200):
        if request.POST.get("presentation") == "page":
            return render_landing(
                request, case=case, result=data if status == 200 else None,
                error=data.get("error"), status=status,
            )
        return JsonResponse(data, status=status)

    if os.getenv("REALMPROOF_ISOLATED_GUESTS") != "1":
        return respond({"error": "The public runner is unavailable on this deployment."}, status=503)
    if case is None:
        return respond({"error": "Choose a bundled transfer scenario."}, status=400)
    if not preview_slots.acquire(blocking=False):
        return respond({"error": "The runner is busy. Try again in a moment."}, status=429)
    try:
        observed, evidence = engine.execute(case["inputs"])
    except TimeoutExpired:
        return respond({"error": "The Gno execution timed out. Please retry."}, status=504)
    except (OSError, RuntimeError, ValueError):
        logger.exception("Landing preview Gno execution failed")
        return respond({"error": "The local Gno runner could not complete this scenario."}, status=503)
    finally:
        preview_slots.release()
    result = evaluate(case["expected"], observed)
    return respond({
        "observed": observed,
        "verdict": result.status,
        "mismatches": list(result.evidence["mismatches"]),
        "duration_ms": evidence["duration_ms"],
        "source_sha256": evidence["source_sha256"],
        "harness_sha256": evidence["harness_sha256"],
    })
