from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .views import membership_for
from .native_catalog import inventory, summarize, ROOTS

@login_required
@require_GET
def overview(request, slug):
    member = membership_for(request, slug)
    rows, truncated = inventory()
    query = request.GET.get("q", "")[:150].strip()
    kind = request.GET.get("kind", "")
    scope = request.GET.get("scope", "")
    filtered = [r for r in rows if (not kind or r["kind"] == kind)
                and (not scope or r["scope"] == scope)
                and (not query or query.casefold() in (r["file"]+" "+r["name"]).casefold())]
    page = Paginator(filtered, 40).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "studio/native_catalog.html", {"member":member,"metrics":summarize(rows),
        "page":page,"query":query,"kind":kind,"scope":scope,"scopes":ROOTS,"truncated":truncated,
        "params":params.urlencode(),"filtered_count":len(filtered)})
