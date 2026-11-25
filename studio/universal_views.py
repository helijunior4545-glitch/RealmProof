from uuid import UUID
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from .views import membership_for
from .models import AuditEvent, UniversalJob
from .universal_queue import enqueue, cancel, QuotaExceeded
from .universal import SUITES, catalog

def snapshot(org):
    qs = UniversalJob.objects.filter(organization=org)
    counts = dict(qs.values("status").annotate(n=Count("pk")).values_list("status", "n"))
    jobs = list(qs.order_by("-created_at")[:20])
    for job in jobs:
        job.planned = SUITES[job.suite].checks if job.suite in SUITES else 0
        job.observed = len(job.result.get("rows", [])) if job.status != "running" else job.result.get("observed_checks", 0)
        job.duration = round((job.finished_at-job.started_at).total_seconds(), 2) if job.finished_at and job.started_at else None
    return counts, jobs

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def overview(request, slug):
    member = membership_for(request, slug, write=request.method == "POST")
    if request.method == "POST":
        try:
            if request.POST.get("cancel"):
                try:
                    job_id = UUID(request.POST["cancel"])
                except ValueError:
                    raise Http404
                if cancel(member, job_id):
                    messages.success(request, "Queued job cancelled.")
                else:
                    messages.warning(request, "Job is no longer cancellable.")
            else:
                key = request.POST.get("suite")
                if key not in SUITES:
                    raise Http404
                enqueue(member, key)
                messages.success(request, "Suite accepted; an existing active request is reused.")
        except QuotaExceeded as exc:
            messages.error(request, str(exc))
        except PermissionError:
            raise PermissionDenied
        return redirect("studio:universal", slug=slug)
    counts, jobs = snapshot(member.organization)
    history = AuditEvent.objects.filter(organization=member.organization, action="universal.suite").order_by("-created_at")[:10]
    context = {"member": member, "suites": SUITES.values(), "categories": catalog(), "history": history, "jobs": jobs, "counts": counts}
    if request.GET.get("fragment") == "monitor":
        return render(request, "studio/universal_monitor.html", context)
    return render(request, "studio/universal.html", context)
