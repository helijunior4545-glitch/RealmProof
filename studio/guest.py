"""Public entry. Private workspaces require an authenticated identity."""
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

@require_GET
def entry(request):
    if request.user.is_authenticated:
        return redirect("studio:dashboard")
    return render(request, "studio/guest_entry.html")

@require_POST
def start(request):
    return redirect("login")
