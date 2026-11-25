from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .views import membership_for
from .models import AuditEvent
from .universal import SUITES, catalog, execute

@login_required
@require_http_methods(["GET", "POST"])
def overview(request, slug):
    member = membership_for(request, slug, write=request.method == "POST")
    if request.method == "POST":
        key = request.POST.get("suite")
        if key not in SUITES:
            raise Http404
        # Execute only fixed bundled fixtures. No user-supplied source or commands.
        result = execute(key)
        AuditEvent.objects.create(organization=member.organization, actor=request.user,
                                  action="universal.suite", target=key, details=result)
        return redirect("studio:universal", slug=slug)
    history = AuditEvent.objects.filter(organization=member.organization,
                                        action="universal.suite").order_by("-created_at")[:10]
    return render(request, "studio/universal.html", {"member": member, "suites": SUITES.values(),
                  "categories": catalog(), "history": history})
