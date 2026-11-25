"""Account-free entry into the existing tenant-scoped console."""
import uuid
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from .models import Organization, Membership, Project, Scenario
from .engine import CASES

@require_GET
def entry(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    return render(request, "studio/guest_entry.html")

@require_POST
def start(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    token = uuid.uuid4().hex
    with transaction.atomic():
        user = get_user_model().objects.create_user(username="guest_" + token, password=None)
        org = Organization.objects.create(name="Personal verification lab", slug="guest-" + token)
        Membership.objects.create(user=user, organization=org, role="owner")
        project = Project.objects.create(organization=org, name="Transfer verification lab", description="Explore the bundled Gno transfer fixture. Local Gno execution requires the CLI; manual evidence is not on-chain verification.")
        for name, family, balance, amount, authorized, status, final in CASES:
            Scenario.objects.create(organization=org, project=project, name=name, family=family, objective="Verify transfer behavior and final balance.", input_data={"engine":"transfer","balance":balance,"amount":amount,"authorized":authorized}, expected={"status":status,"balance":final,"state_changed":final != balance})
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session["realmproof_guest"] = True
    request.session.set_expiry(86400)
    if request.POST.get("mode") == "review":
        return redirect("studio:project", slug=org.slug, project_id=project.pk)
    return redirect("studio:dashboard")
