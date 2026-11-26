from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from .models import Organization, Membership, Project, SourceTestDraft, SourceSnapshot
from .source_discovery import capture
from .orchestration import confirm, proposal_key
from .execution_planning import prepare

class ExecutionPlanningTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="planner")
        org = Organization.objects.create(name="Planning", slug="planning")
        self.member = Membership.objects.create(user=user, organization=org, role="editor")
        project = Project.objects.create(organization=org, name="Project")
        self.snapshot, _ = capture(self.member, project.pk, {"a.gno": "package a"})
        proposal = {"rule": "index_boundary", "function": "A", "line": 2}
        with patch("studio.orchestration.analyze", return_value={"recommendations": {"items": [proposal]}}):
            self.draft = confirm(self.member, project.pk, self.snapshot.pk, "a.gno", proposal_key(proposal), {"accepted": False})

    def test_preflight_never_claims_execution(self):
        plan = prepare(self.member, self.draft.pk)
        self.assertEqual(plan["execution"], "not_executed")
        self.assertEqual(plan["verdict"], "inconclusive")
        self.assertFalse(plan["verified_on_chain"])
        self.assertEqual(plan["source_digest"], self.draft.source_digest)
        self.assertEqual(plan, prepare(self.member, self.draft.pk))

    def test_revoked_role(self):
        Membership.objects.filter(pk=self.member.pk).update(role="viewer")
        with self.assertRaises(PermissionDenied):
            prepare(self.member, self.draft.pk)

    def test_foreign_tenant(self):
        org = Organization.objects.create(name="Other", slug="other-planning")
        member = Membership.objects.create(user=self.member.user, organization=org, role="editor")
        with self.assertRaises(SourceTestDraft.DoesNotExist):
            prepare(member, self.draft.pk)

    def test_changed_source(self):
        files = self.snapshot.files
        files["a.gno"]["source"] = "package changed"
        SourceSnapshot.objects.filter(pk=self.snapshot.pk).update(files=files)
        with self.assertRaises(ValidationError):
            prepare(self.member, self.draft.pk)

    def test_changed_proposal(self):
        SourceTestDraft.objects.filter(pk=self.draft.pk).update(proposal={"rule": "changed"})
        with self.assertRaises(ValidationError):
            prepare(self.member, self.draft.pk)

    def test_missing_assertions(self):
        SourceTestDraft.objects.filter(pk=self.draft.pk).update(expected={})
        with self.assertRaises(ValidationError):
            prepare(self.member, self.draft.pk)
