"""Provision one independent, non-staff reviewer with a prepared project."""
import getpass
import uuid
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from studio.models import Organization, Membership, Project, Scenario
from studio.engine import CASES

class Command(BaseCommand):
    help = "Create a private hackathon reviewer account and six prepared scenarios."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise CommandError("Username already exists.")
        password = getpass.getpass("Reviewer password: ")
        if password != getpass.getpass("Confirm password: "):
            raise CommandError("Passwords do not match.")
        try:
            validate_password(password, User(username=username))
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
            org = Organization.objects.create(name="Hackathon Demo", slug="review-" + uuid.uuid4().hex)
            Membership.objects.create(user=user, organization=org, role="editor")
            project = Project.objects.create(organization=org, name="Transfer verification lab", description="Six prepared scenarios for the hackathon review. Gno CLI availability is required for local execution.")
            for name, family, balance, amount, authorized, status, final in CASES:
                Scenario.objects.create(organization=org, project=project, name=name, family=family, objective="Verify transfer behavior and final balance.", input_data={"engine":"transfer","balance":balance,"amount":amount,"authorized":authorized}, expected={"status":status,"balance":final,"state_changed":final != balance})
        self.stdout.write(self.style.SUCCESS("Reviewer created. Share credentials privately."))
