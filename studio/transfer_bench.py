"""Run the bundled transfer fixture without provisioning a workspace."""

import os
from subprocess import TimeoutExpired
from threading import BoundedSemaphore

from django import forms
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from . import engine
from .services import evaluate

LIMIT = 10**12
slots = BoundedSemaphore(2)


class TransferForm(forms.Form):
    balance = forms.IntegerField(min_value=0, max_value=LIMIT)
    amount = forms.IntegerField(min_value=-LIMIT, max_value=LIMIT)
    authorized = forms.TypedChoiceField(
        choices=[("true", "Authorized"), ("false", "Unauthorized")],
        coerce=lambda value: value == "true",
    )
    status = forms.ChoiceField(choices=[("success", "Accepted"), ("rejected", "Rejected")])
    final_balance = forms.IntegerField(min_value=0, max_value=LIMIT)


@never_cache
@require_http_methods(["GET", "POST"])
def bench(request):
    if request.method == "GET":
        return render(request, "studio/test_bench.html", {
            "execution_enabled": os.getenv("REALMPROOF_ISOLATED_GUESTS") == "1",
        })
    if os.getenv("REALMPROOF_ISOLATED_GUESTS") != "1":
        return JsonResponse({"error": "Guest execution is unavailable in this deployment."}, status=503)

    form = TransferForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Use whole numbers within the allowed range and select valid outcomes."}, status=400)

    data = form.cleaned_data
    inputs = {key: data[key] for key in ("balance", "amount", "authorized")}
    expected = {"status": data["status"], "balance": data["final_balance"]}
    if not slots.acquire(blocking=False):
        return JsonResponse({"error": "The runner is busy. Try again in a moment."}, status=429)
    try:
        observed, evidence = engine.execute(inputs)
    except TimeoutExpired:
        return JsonResponse({"error": "The Gno run timed out. Try again."}, status=504)
    except (OSError, RuntimeError):
        return JsonResponse({"error": "The local Gno runner could not complete this test."}, status=503)
    finally:
        slots.release()

    result = evaluate(expected, observed)
    return JsonResponse({
        "inputs": inputs,
        "expected": expected,
        "observed": observed,
        "verdict": result.status,
        "mismatches": list(result.evidence["mismatches"]),
        "evidence": {key: evidence[key] for key in (
            "duration_ms", "source_sha256", "harness_sha256", "verified_on_chain",
        )},
    })
