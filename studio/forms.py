"""Intent-driven forms for the RealmProof console."""
from django import forms
from .models import Project, Scenario


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Treasury realm verification"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "What do you want to verify in this project?"}),
        }


class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = ("name", "family", "objective", "input_data", "expected")
        labels = {
            "name": "Scenario name",
            "family": "Test family",
            "objective": "Intended behavior",
            "input_data": "Inputs and initial state (JSON)",
            "expected": "Expected outcome (JSON)",
        }
        help_texts = {
            "objective": "Describe the behavior you expect, not an execution trace.",
            "input_data": 'Example: {"balance": 100, "amount": 150}',
            "expected": 'Example: {"status": "reverted", "balance": 100}',
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Reject transfer above available balance"}),
            "objective": forms.Textarea(attrs={"rows": 4, "placeholder": "The transfer must fail and the account balance must remain unchanged."}),
            "input_data": forms.Textarea(attrs={"rows": 7, "class": "code-input", "spellcheck": "false"}),
            "expected": forms.Textarea(attrs={"rows": 7, "class": "code-input", "spellcheck": "false"}),
        }
