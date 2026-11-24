# Generated for RealmProof initial schema.
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("role", models.CharField(max_length=12, default="viewer", choices=[("owner", "Owner"), ("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")])),
                ("organization", models.ForeignKey(to="studio.organization", on_delete=django.db.models.deletion.CASCADE, related_name="memberships")),
                ("user", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name="realmproof_memberships")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("organization", "user"), name="unique_org_membership")]},
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.ForeignKey(to="studio.organization", on_delete=django.db.models.deletion.CASCADE, related_name="projects")),
            ],
        ),
        migrations.CreateModel(
            name="Scenario",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("name", models.CharField(max_length=180)),
                ("family", models.CharField(max_length=20, default="valid", choices=[("valid", "Valid behavior"), ("invalid", "Invalid inputs"), ("permission", "Permissions"), ("boundary", "Boundary conditions"), ("state", "State and repetition"), ("integration", "Integration"), ("regression", "Regression"), ("property", "Property testing"), ("performance", "Performance")])),
                ("objective", models.TextField()),
                ("input_data", models.JSONField(default=dict)),
                ("expected", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.ForeignKey(to="studio.organization", on_delete=django.db.models.deletion.CASCADE, related_name="scenarios")),
                ("project", models.ForeignKey(to="studio.project", on_delete=django.db.models.deletion.CASCADE, related_name="scenarios")),
            ],
        ),
        migrations.CreateModel(
            name="TestRun",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("status", models.CharField(max_length=16, default="pending", choices=[("pending", "Pending"), ("passed", "Passed"), ("failed", "Failed"), ("inconclusive", "Inconclusive"), ("error", "Infrastructure error")])),
                ("execution_status", models.CharField(max_length=48, default="not_executed")),
                ("input_snapshot", models.JSONField(default=dict)),
                ("expected_snapshot", models.JSONField(default=dict)),
                ("observed", models.JSONField(default=dict)),
                ("evidence", models.JSONField(default=dict)),
                ("reason", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(null=True, blank=True)),
                ("initiated_by", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ("organization", models.ForeignKey(to="studio.organization", on_delete=django.db.models.deletion.CASCADE, related_name="runs")),
                ("scenario", models.ForeignKey(to="studio.scenario", on_delete=django.db.models.deletion.PROTECT, related_name="runs")),
            ],
            options={
                "indexes": [models.Index(fields=["organization", "-started_at"], name="studio_test_organiz_6ce6cf_idx")],
                "constraints": [models.CheckConstraint(condition=models.Q(status__in=["pending", "passed", "failed", "inconclusive", "error"]), name="valid_run_status")],
            },
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("action", models.CharField(max_length=100)),
                ("target", models.CharField(max_length=200)),
                ("details", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT)),
                ("organization", models.ForeignKey(to="studio.organization", on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={"indexes": [models.Index(fields=["organization", "-created_at"], name="studio_audi_organiz_7a1263_idx")]},
        ),
    ]
