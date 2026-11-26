"""Tenant-scoped testing data with explicit membership authorization."""
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def uid():
    return uuid.uuid4()


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    ROLE_CHOICES = [("owner", "Owner"), ("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="realmproof_memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="viewer")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_org_membership")]


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    FAMILIES = [
        ("valid", "Valid behavior"), ("invalid", "Invalid inputs"), ("permission", "Permissions"),
        ("boundary", "Boundary conditions"), ("state", "State and repetition"),
        ("integration", "Integration"), ("regression", "Regression"),
        ("property", "Property testing"), ("performance", "Performance"),
    ]
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="scenarios")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="scenarios")
    name = models.CharField(max_length=180)
    family = models.CharField(max_length=20, choices=FAMILIES, default="valid")
    objective = models.TextField()
    input_data = models.JSONField(default=dict, blank=True)
    expected = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.project_id and self.organization_id and self.project.organization_id != self.organization_id:
            raise ValidationError("The scenario and project must belong to the same organization.")
        if not isinstance(self.input_data, dict) or not isinstance(self.expected, dict):
            raise ValidationError("Scenario input and expected result must be JSON objects.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TestRun(models.Model):
    STATUS = [
        ("pending", "Pending"), ("passed", "Passed"), ("failed", "Failed"),
        ("inconclusive", "Inconclusive"), ("error", "Infrastructure error"),
    ]
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="runs")
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="runs")
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=STATUS, default="pending")
    execution_status = models.CharField(max_length=48, default="not_executed")
    input_snapshot = models.JSONField(default=dict, blank=True)
    expected_snapshot = models.JSONField(default=dict, blank=True)
    observed = models.JSONField(default=dict, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["organization", "-started_at"], name="studio_test_organiz_6ce6cf_idx")]
        constraints = [models.CheckConstraint(condition=Q(status__in=["pending", "passed", "failed", "inconclusive", "error"]), name="valid_run_status")]

    def clean(self):
        if self.scenario_id and self.organization_id and self.scenario.organization_id != self.organization_id:
            raise ValidationError("The run and scenario must belong to the same organization.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=200)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["organization", "-created_at"], name="studio_audi_organiz_7a1263_idx")]


class UniversalJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    suite = models.CharField(max_length=40)
    status = models.CharField(max_length=16, default="queued")
    token = models.UUIDField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    result = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "created_at"], name="rp_job_queue_idx")]
        constraints = [models.CheckConstraint(condition=Q(status__in=["queued", "running", "completed", "error", "cancelled"]), name="rp_job_valid_status"),
                       models.UniqueConstraint(fields=["organization"], condition=Q(status="running"), name="rp_job_one_running")]


class SourceSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="source_snapshots")
    digest = models.CharField(max_length=64)
    files = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "digest"], name="rp_source_unique_digest")]


class SourceTestDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uid, editable=False)
    snapshot = models.ForeignKey(SourceSnapshot, on_delete=models.PROTECT, related_name="test_drafts")
    path = models.CharField(max_length=240)
    source_digest = models.CharField(max_length=64)
    proposal_key = models.CharField(max_length=64)
    proposal = models.JSONField()
    expected = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["snapshot", "path", "proposal_key"], name="rp_unique_source_draft")]
