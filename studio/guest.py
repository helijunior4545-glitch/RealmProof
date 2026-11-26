"""Public demo entry with server-side credentials and fail-closed authorization."""
import os
import logging
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .models import Membership

logger = logging.getLogger(__name__)

@never_cache
@require_GET
def entry(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    return render(request, "studio/guest_entry.html")

@never_cache
@require_POST
def start(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    username = os.getenv("REALMPROOF_DEMO_USERNAME", "")
    password = os.getenv("REALMPROOF_DEMO_PASSWORD", "")
    user = authenticate(request, username=username, password=password) if username == "hackathon_demo_public" and password else None
    if user and user.is_active and not user.is_staff and not user.is_superuser:
        memberships = list(Membership.objects.filter(user=user).select_related("organization")[:2])
        if len(memberships) == 1 and memberships[0].organization.slug.startswith("review-") and memberships[0].role == "editor":
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
