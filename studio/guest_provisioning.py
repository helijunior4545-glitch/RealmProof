"""Bounded opt-in guest provisioning."""
import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Organization, Membership, Project, Scenario
from .engine import CASES

PREFIX = "rp_guest_"
CAP = 100

@transaction.atomic
def provision(template, name="Guest verification workspace", description="Prepared trusted transfer scenarios.", starter="transfer"):
    User = get_user_model()
    anchor = User.objects.select_for_update().get(pk=template.pk)
    memberships = list(Membership.objects.filter(user=anchor).select_related("organization")[:2])
    if (not anchor.is_active or anchor.is_staff or anchor.is_superuser
            or len(memberships) != 1 or memberships[0].role != "editor"
            or not memberships[0].organization.slug.startswith("review-")):
        return None
    if User.objects.filter(username__startswith=PREFIX).count() >= CAP:
        return None
    key = uuid.uuid4().hex
    user = User.objects.create_user(username=PREFIX + key, password=None)
    org = Organization.objects.create(name=name, slug="guest-" + key)
    Membership.objects.create(user=user, organization=org, role="editor")
    project = Project.objects.create(organization=org, name="Transfer verification lab" if starter == "transfer" else "New verification project", description=description)
    for name, family, balance, amount, authorized, status, final in (CASES if starter == "transfer" else []):
        Scenario.objects.create(organization=org, project=project, name=name, family=family,
            objective="Verify transfer behavior and final balance.",
            input_data={"engine":"transfer","balance":balance,"amount":amount,"authorized":authorized},
            expected={"status":status,"balance":final,"state_changed":final != balance})
    return user, org, project
