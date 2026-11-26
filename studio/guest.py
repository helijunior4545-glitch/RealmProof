"""Public demo entry with server-side credentials and fail-closed authorization."""
import os
import logging
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import Http404
from .views import membership_for
from .models import Project
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .models import Membership

logger = logging.getLogger(__name__)

def studio_destination(request):
    if not request.user.is_authenticated:
        return None
    for slug in Membership.objects.filter(user=request.user).order_by("organization__slug").values_list("organization__slug", flat=True):
        try:
            member = membership_for(request, slug)
        except Http404:
            continue
        project = Project.objects.filter(organization=member.organization).order_by("-created_at", "pk").first()
        if project:
            return reverse("studio:project", kwargs={"slug": slug, "project_id": project.pk})
    return None

@never_cache
@require_GET
def entry(request):
    if request.user.is_authenticated:
        return redirect(studio_destination(request) or "studio:dashboard")
    return render(request, "studio/guest_entry.html", {
        "guest_enabled": os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1",
    })


@never_cache
@require_POST
def start(request):
    if request.user.is_authenticated:
        return redirect(studio_destination(request) or "studio:dashboard")
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
                    return render(request, "studio/guest_entry.html", {"guest_error": "All guest workspaces are occupied."}, status=503)
                visitor, org, project = result
                login(request, visitor, backend="django.contrib.auth.backends.ModelBackend")
                request.session.set_expiry(3600)
                request.session["realmproof_guest"] = True
                return redirect("studio:project", slug=org.slug, project_id=project.pk)
            login(request, user)
            request.session.set_expiry(3600)
            request.session["realmproof_guest"] = True
            organization = memberships[0].organization
            project = Project.objects.filter(organization=organization, name="Transfer verification lab").order_by("created_at").first()
            if project:
                return redirect("studio:project", slug=organization.slug, project_id=project.pk)
            return redirect("studio:organization", slug=organization.slug)
    logger.warning("Demo launch rejected: configured=%s authenticated=%s", bool(username and password), bool(user))
    return render(request, "studio/guest_entry.html", {
        "guest_error": "Guest lab unavailable.",
    }, status=503)
