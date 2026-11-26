"""Public demo entry with server-side credentials and fail-closed authorization."""
import os
import logging
import secrets
from django import forms
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import Http404
from .views import membership_for
from .models import Project
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .models import Membership

logger = logging.getLogger(__name__)

class WorkspaceForm(forms.Form):
    name = forms.CharField(max_length=120, label="Workspace name")
    description = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 3}))
    starter = forms.ChoiceField(choices=[("transfer", "Transfer verification lab"), ("empty", "Empty project")])

def suggested_form():
    return WorkspaceForm(initial={"name": secrets.choice(["Atlas", "Orion", "Meridian", "Vector", "Nova"]) + " Verification " + secrets.token_hex(2).upper(),
        "description": "Explore contract behavior, define expectations and inspect reproducible evidence.", "starter": "transfer"})

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
    # Returning users go straight to their actual workbench, not the explainer.
    if request.user.is_authenticated:
        return redirect(studio_destination(request) or "studio:dashboard")
    return render(request, "studio/public_entry.html", {
        "form": suggested_form(),
        "isolated_guest": os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1",
    })


@never_cache
@login_required
@require_GET
def engineering(request):
    # Do not let an expired isolated guest use an internal route indefinitely.
    if request.user.username.startswith("rp_guest_") and not studio_destination(request):
        raise Http404
    return render(request, "studio/guest_entry.html", {
        "studio_url": studio_destination(request),
        "dashboard_url": reverse("studio:dashboard"),
        "isolated_guest": False,
    })

@never_cache
@require_POST
def start(request):
    if request.user.is_authenticated:
        return redirect(studio_destination(request) or "studio:dashboard")
    form = WorkspaceForm(request.POST) if request.POST.get("name") is not None else suggested_form()
    if form.is_bound and not form.is_valid():
        return render(request, "studio/public_entry.html", {"form": form, "isolated_guest": os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1"}, status=400)
    username = os.getenv("REALMPROOF_DEMO_USERNAME", "")
    password = os.getenv("REALMPROOF_DEMO_PASSWORD", "")
    user = authenticate(request, username=username, password=password) if username == "hackathon_demo_public" and password else None
    if user and user.is_active and not user.is_staff and not user.is_superuser:
        memberships = list(Membership.objects.filter(user=user).select_related("organization")[:2])
        if len(memberships) == 1 and memberships[0].organization.slug.startswith("review-") and memberships[0].role == "editor":
            if os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1":
                from .guest_provisioning import provision
                result = provision(user, **(form.cleaned_data if form.is_bound else form.initial))
                if result is None:
                    messages.error(request, "Guest capacity reached. Please try again later.")
                    return redirect("studio:public_demo")
                visitor, org, project = result
                login(request, visitor, backend="django.contrib.auth.backends.ModelBackend")
                request.session.set_expiry(3600)
                request.session["realmproof_guest"] = True
                return redirect("studio:project", slug=org.slug, project_id=project.pk)
            login(request, user)
            request.session.set_expiry(3600)
            request.session['realmproof_guest'] = True
            from .models import Project
            project = Project.objects.filter(organization=memberships[0].organization, name="Transfer verification lab").order_by("created_at").first()
            if project:
                return redirect("studio:project", slug=memberships[0].organization.slug, project_id=project.pk)
            return redirect("studio:organization", slug=memberships[0].organization.slug)
    logger.warning("Demo launch rejected: configured=%s authenticated=%s", bool(username and password), bool(user))
    messages.error(request, "Demo access is temporarily unavailable. Please try again later.")
    return redirect("studio:public_demo")
