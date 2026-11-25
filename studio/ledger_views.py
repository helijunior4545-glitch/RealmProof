from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .views import membership_for
from . import ledger_lab
import subprocess

@login_required
@require_http_methods(["GET", "POST"])
def overview(request, slug):
    member = membership_for(request, slug, write=request.method == "POST")
    observed = {}
    context = {"member": member}
    if request.method == "POST":
        try:
            observed, source, harness, output = ledger_lab.run()
            context.update(source_hash=source, harness_hash=harness, output=output)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            context["error"] = str(exc)
    groups = {}
    passed = failed = 0
    for key, group, title, expression, expected in ledger_lab.CASES:
        actual = observed.get(key)
        status = "pending" if actual is None else "passed" if actual == expected else "failed"
        passed += status == "passed"
        failed += status == "failed"
        groups.setdefault(group, []).append({"title": title, "expression": expression, "expected": expected, "actual": actual, "status": status})
    context.update(groups=groups, total=len(ledger_lab.CASES), passed=passed, failed=failed)
    return render(request, "studio/ledger_lab.html", context)
