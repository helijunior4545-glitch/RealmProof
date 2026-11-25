"""Database-backed queue for trusted suites; PostgreSQL required for concurrent workers."""
import uuid
from datetime import timedelta
from django.db import transaction, connection
from django.utils import timezone
from .models import Organization, Membership, UniversalJob, AuditEvent
from .universal import SUITES, execute
from .failure_intelligence import classify

MAX_ACTIVE = 4
MAX_DAILY = 30
LEASE = timedelta(minutes=10)

class QuotaExceeded(Exception):
    pass

@transaction.atomic
def enqueue(member, key):
    if key not in SUITES:
        raise ValueError("Unknown suite")
    org = Organization.objects.select_for_update().get(pk=member.organization_id)
    if not Membership.objects.filter(pk=member.pk, organization=org, role__in=["owner", "admin", "editor"]).exists():
        raise PermissionError("Write membership required")
    jobs = UniversalJob.objects.filter(organization=org)
    existing = jobs.filter(suite=key, status__in=["queued", "running"]).order_by("created_at").first()
    if existing:
        return existing
    if jobs.filter(status__in=["queued", "running"]).count() >= MAX_ACTIVE:
        raise QuotaExceeded("Active queue limit reached.")
    if jobs.filter(created_at__gte=timezone.now()-timedelta(days=1)).count() >= MAX_DAILY:
        raise QuotaExceeded("Rolling 24-hour execution limit reached.")
    return UniversalJob.objects.create(organization=org, actor=member.user, suite=key)

def error_result(reason):
    return {"execution": "error", "verdict": "inconclusive", "rows": [], "reason": reason, "verified_on_chain": False}

@transaction.atomic
def finish(job_id, token, result):
    job = UniversalJob.objects.select_for_update().filter(pk=job_id, token=token, status="running").first()
    if not job:
        return False
    result = dict(result, failure_category=classify(result))
    job.result = result
    job.status = "completed" if result["execution"] == "completed" else "error"
    job.finished_at = timezone.now()
    job.save(update_fields=["result", "status", "finished_at"])
    AuditEvent.objects.create(organization=job.organization, actor=job.actor,
                              action="universal.suite", target=job.suite, details=result)
    return True

def expire():
    for job_id, token in UniversalJob.objects.filter(status="running", started_at__lt=timezone.now()-LEASE).values_list("pk", "token")[:100]:
        finish(job_id, token, error_result("Worker lease expired; execution outcome unknown."))

@transaction.atomic
def claim():
    candidates = UniversalJob.objects.filter(status="queued").order_by("created_at").values_list("organization_id", flat=True)[:100]
    for org_id in list(dict.fromkeys(candidates)):
        orgs = Organization.objects.filter(pk=org_id)
        if connection.features.has_select_for_update_skip_locked:
            orgs = orgs.select_for_update(skip_locked=True)
        else:
            orgs = orgs.select_for_update()
        if not orgs.first():
            continue
        if UniversalJob.objects.filter(organization_id=org_id, status="running").exists():
            continue
        job = UniversalJob.objects.select_for_update().filter(organization_id=org_id, status="queued").order_by("created_at").first()
        if job:
            job.status = "running"
            job.token = uuid.uuid4()
            job.started_at = timezone.now()
            job.save(update_fields=["status", "token", "started_at"])
            return job
    return None

def process_one():
    expire()
    job = claim()
    if not job:
        return False
    if not Membership.objects.filter(organization=job.organization, user=job.actor, role__in=["owner", "admin", "editor"]).exists():
        result = error_result("Permission denied: membership revoked.")
    else:
        try:
            result = execute(job.suite, progress=lambda count: UniversalJob.objects.filter(pk=job.pk, token=job.token, status="running").update(result={"observed_checks": count}))
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Universal job failed: %s", job.pk)
            result = error_result("Unexpected worker exception; inspect server logs.")
    finish(job.pk, job.token, result)
    return True


@transaction.atomic
def cancel(member, job_id):
    org = Organization.objects.select_for_update().get(pk=member.organization_id)
    if not Membership.objects.filter(pk=member.pk, organization=org, role__in=["owner", "admin", "editor"]).exists():
        raise PermissionError("Write membership required")
    job = UniversalJob.objects.select_for_update().filter(pk=job_id, organization=org, status="queued").first()
    if not job:
        return False
    job.status = "cancelled"
    job.finished_at = timezone.now()
    job.result = {"execution": "not_executed", "verdict": "inconclusive", "rows": [], "verified_on_chain": False}
    job.save(update_fields=["status", "finished_at", "result"])
    AuditEvent.objects.create(organization=org, actor=member.user, action="universal.cancelled", target=str(job.pk), details={"suite": job.suite})
    return True
