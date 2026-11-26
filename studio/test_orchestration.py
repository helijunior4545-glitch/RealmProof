from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from .models import Organization, Membership, Project, SourceTestDraft, AuditEvent, SourceSnapshot
from .source_discovery import capture
from .orchestration import confirm, proposal_key

class OrchestrationTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="draft-editor")
        org = Organization.objects.create(name="Drafts", slug="drafts")
        self.member = Membership.objects.create(user=user, organization=org, role="editor")
        self.project = Project.objects.create(organization=org, name="Project")
        self.snapshot, _ = capture(self.member, self.project.pk, {"a.gno": "package a"})
        self.proposal = {"rule": "index_boundary", "function": "A", "line": 2, "expected": None}
        self.key = proposal_key(self.proposal)

    def save_draft(self, expected):
        return confirm(self.member, self.project.pk, self.snapshot.pk, "a.gno", self.key, expected)

    @patch("studio.orchestration.analyze")
    def test_confirm_idempotent_and_audited(self, analyze):
        analyze.return_value = {"recommendations": {"items": [self.proposal]}}
        draft = self.save_draft({"accepted": False})
        self.assertEqual(draft.pk, self.save_draft({"accepted": False}).pk)
        self.assertEqual(draft.source_digest, self.snapshot.files["a.gno"]["sha256"])
        self.assertEqual(AuditEvent.objects.filter(action="source_draft_confirmed").count(), 1)
        with self.assertRaises(ValidationError):
            self.save_draft({"accepted": True})

    def test_empty_intent_rejected(self):
        with self.assertRaises(ValidationError):
            self.save_draft({})
        self.assertFalse(SourceTestDraft.objects.exists())

    def test_revoked_write_rejected(self):
        Membership.objects.filter(pk=self.member.pk).update(role="viewer")
        with self.assertRaises(PermissionDenied):
            self.save_draft({"accepted": False})

    @patch("studio.orchestration.analyze", return_value={})
    def test_unknown_proposal_rejected(self, analyze):
        with self.assertRaises(ValidationError):
            self.save_draft({"accepted": False})

    def test_foreign_snapshot_rejected(self):
        other = Project.objects.create(organization=self.project.organization, name="Other")
        with self.assertRaises(SourceSnapshot.DoesNotExist):
            confirm(self.member, other.pk, self.snapshot.pk, "a.gno", self.key, {"accepted": False})
