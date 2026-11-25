"""Prepare the local demo without exposing credentials to the browser."""
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from studio.models import Organization, Membership, Project, Scenario
from studio.engine import CASES

class Command(BaseCommand):
    help = "Migrate and provision the local-only demo account."

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "realmproof.settings_local" or settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("This command requires explicit local SQLite settings.")
        call_command("migrate", interactive=False)
        username = os.environ["REALMPROOF_DEMO_USERNAME"]
        password = os.environ["REALMPROOF_DEMO_PASSWORD"]
        with transaction.atomic():
            user, _ = get_user_model().objects.get_or_create(username=username)
            if user.is_staff or user.is_superuser:
                raise CommandError("Refusing to modify a privileged account.")
            memberships = list(Membership.objects.filter(user=user).select_related("organization")[:2])
            if memberships:
                if len(memberships) != 1 or memberships[0].role != "editor" or not memberships[0].organization.slug.startswith("review-"):
                    raise CommandError("Existing account has incompatible memberships.")
                org = memberships[0].organization
            else:
                import uuid
                org = Organization.objects.create(name="Local Hackathon Demo", slug="review-" + uuid.uuid4().hex)
                Membership.objects.create(user=user, organization=org, role="editor")
            user.is_active = True
            if not user.check_password(password):
                user.set_password(password)
            user.save()
            project, _ = Project.objects.get_or_create(organization=org, name="Transfer verification lab", defaults={"description":"Local Gno verification scenarios."})
            for name, family, balance, amount, authorized, status, final in CASES:
                Scenario.objects.get_or_create(organization=org, project=project, name=name, defaults={"family":family,"objective":"Verify transfer behavior and final balance.","input_data":{"engine":"transfer","balance":balance,"amount":amount,"authorized":authorized},"expected":{"status":status,"balance":final,"state_changed":final != balance}})
        self.stdout.write(self.style.SUCCESS("Local demo ready. Launch Hackathon Demo in the browser."))
