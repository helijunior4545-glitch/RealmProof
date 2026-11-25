from django import forms
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .engine import CASES

class DemoForm(forms.Form):
    balance = forms.IntegerField(min_value=0, max_value=10**12, initial=100)
    amount = forms.IntegerField(min_value=-10**12, max_value=10**12, initial=25)
    authorized = forms.TypedChoiceField(choices=[("yes","Yes"),("no","No")], coerce=lambda v: v == "yes", initial="yes")
    expected_status = forms.ChoiceField(choices=[("success","Success"),("rejected","Rejected")], initial="success")
    expected_balance = forms.IntegerField(min_value=0, max_value=10**12, initial=75)

@require_http_methods(["GET", "POST"])
def home(request):
    form = DemoForm(request.POST if request.method == "POST" else None)
    result = None
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        accepted = d["authorized"] and 0 < d["amount"] <= d["balance"]
        observed = {"status": "success" if accepted else "rejected", "balance": d["balance"] - d["amount"] if accepted else d["balance"]}
        expected = {"status": d["expected_status"], "balance": d["expected_balance"]}
        result = {"observed": observed, "expected": expected, "passed": observed == expected}
    response = render(request, "studio/public_demo.html", {"form": form, "result": result, "cases": CASES})
    response["Cache-Control"] = "no-store"
    return response
