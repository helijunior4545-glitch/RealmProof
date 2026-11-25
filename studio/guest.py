"""Public entry and explicitly enabled shared hackathon account."""
import os
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from .models import Membership

@require_GET
def entry(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    return render(request, "studio/guest_entry.html")

@require_POST
def start(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    username = os.getenv("REALMPROOF_DEMO_USERNAME", "")
    password = os.getenv("REALMPROOF_DEMO_PASSWORD", "")
    user = authenticate(request, username=username, password=password) if username and password else None
    if user and user.is_active and not user.is_staff and not user.is_superuser and user.username.startswith("hackathon_demo_"):
        memberships = list(Membership.objects.filter(user=user).select_related("organization")[:2])
        if len(memberships) == 1 and memberships[0].organization.slug.startswith("review-") and memberships[0].role == "editor":
            login(request, user)
            request.session.set_expiry(3600)
            return redirect("studio:organization", slug=memberships[0].organization.slug)
    messages.error(request, "The shared demo is not available. You can still explore the reference simulation.")
    return redirect("studio:reference_demo")
