import json
import os
import shutil
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET
from .views import membership_for
from . import chain

@login_required
@require_GET
def overview(request, slug):
    member = membership_for(request, slug)
    network = request.GET.get("network", "testnet")
    digest = request.GET.get("hash", "").strip()
    height = request.GET.get("height", "").strip()
    context = {"height":height,"member":member,"network":network,"digest":digest,"cli_available":bool(shutil.which(os.environ.get("REALMPROOF_GNO_BINARY","gno")))}
    try:
        context["chain_status"] = chain.status(network)
        if digest:
            result = chain.transaction(network,digest,height or None)
            context["transaction"] = result
            context["transaction_json"] = json.dumps(result, indent=2)
    except chain.ChainError as exc:
        context["error"] = str(exc)
    return render(request,"studio/network.html",context)
