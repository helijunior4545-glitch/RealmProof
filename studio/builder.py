from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import Project, Scenario, TestRun
from .views import membership_for, audit

class DemoForm(forms.Form):
    title = forms.CharField(max_length=160)
    description = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows":3}))
    scenario = forms.CharField(max_length=180)
    objective = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows":3}))
    balance = forms.IntegerField(min_value=0,max_value=10**12,initial=100)
    amount = forms.IntegerField(min_value=-10**12,max_value=10**12,initial=25)
    authorized = forms.ChoiceField(choices=[("yes","Authorized"),("no","Unauthorized")])
    expected_status = forms.ChoiceField(choices=[("success","Success"),("rejected","Rejected")])
    expected_balance = forms.IntegerField(min_value=0,max_value=10**12,initial=75)
    expected_change = forms.ChoiceField(choices=[("yes","Changed"),("no","Unchanged")])

@login_required
@require_http_methods(["GET","POST"])
def create(request, slug):
    member = membership_for(request, slug, write=True)
    form = DemoForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            project = Project.objects.create(organization=member.organization,name=d["title"],description=d["description"])
            scenario = Scenario.objects.create(organization=member.organization,project=project,name=d["scenario"],objective=d["objective"],
                input_data={"engine":"transfer","balance":d["balance"],"amount":d["amount"],"authorized":d["authorized"]=="yes"},
                expected={"status":d["expected_status"],"balance":d["expected_balance"],"state_changed":d["expected_change"]=="yes"})
            audit(member.organization,request.user,"demo.custom_created",project.pk)
        return redirect("studio:project",slug=slug,project_id=project.pk)
    return render(request,"studio/builder.html",{"member":member,"form":form})
