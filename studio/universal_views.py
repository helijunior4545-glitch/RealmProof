from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .views import membership_for
from .models import AuditEvent, UniversalJob
from .universal_queue import enqueue, QuotaExceeded
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .universal import SUITES, catalog

@login_required
@require_http_methods(["GET", "POST"])
def overview(request, slug):
    member = membership_for(request, slug, write=request.method == "POST")
    if request.method == "POST":
        key = request.POST.get("suite")
        if key not in SUITES:
            raise Http404
        try:
            enqueue(member, key)
        except QuotaExceeded as exc:
            messages.error(request, str(exc))
        except PermissionError:
            raise PermissionDenied
        else:
            messages.success(request, "Suite queued. Refresh to inspect worker progress.")
        return redirect("studio:universal", slug=slug)
    history = AuditEvent.objects.filter(organization=member.organization,
                                        action="universal.suite").order_by("-created_at")[:10]
    return render(request, "studio/universal.html", {"member": member, "suites": SUITES.values(),
                  "categories": catalog(), "history": history, "jobs": UniversalJob.objects.filter(organization=member.organization).order_by("-created_at")[:20]})
