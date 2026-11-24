from django import forms
from .models import Project, Scenario

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = ("name", "family", "objective", "input_data", "expected")
        widgets = {
            "objective": forms.Textarea(attrs={"rows": 3}),
            "input_data": forms.Textarea(attrs={"rows": 5}),
            "expected": forms.Textarea(attrs={"rows": 5}),
        }
