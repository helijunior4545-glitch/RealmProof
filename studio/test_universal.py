from unittest.mock import patch
from django.test import SimpleTestCase, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Organization, Membership, AuditEvent, UniversalJob
from .universal import SUITES, catalog, execute

class RegistryTests(SimpleTestCase):
    def test_registry_has_fifteen_categories(self):
        self.assertEqual(len(catalog()), 15)
        self.assertEqual(sum(s.checks for s in SUITES.values()), 1787)
        self.assertTrue(next(c for c in catalog() if c["key"] == "fuzz")["suites"])

    @patch("studio.universal.engine.execute")
    def test_transfer_comparison(self, run):
        run.return_value = ({"status": "wrong", "balance": 0, "state_changed": False}, {})
        result = execute("transfer-v1")
        self.assertEqual(result["execution"], "completed")
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual(len(result["rows"]), 6)

    @patch("studio.universal.ledger_lab.run", side_effect=RuntimeError("Unavailable"))
    def test_infrastructure_error_is_not_assertion_failure(self, run):
        result = execute("ledger-v1")
        self.assertEqual(result["execution"], "error")
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["rows"], [])

class TenantTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="universal-user")
        self.org = Organization.objects.create(name="One", slug="universal-one")
        self.other = Organization.objects.create(name="Two", slug="universal-two")
        self.member = Membership.objects.create(user=self.user, organization=self.org, role="editor")
        self.client.force_login(self.user)
        self.url = reverse("studio:universal", args=[self.org.slug])

    @patch("studio.universal_queue.execute")
    def test_persistence_and_isolation(self, run):
        run.return_value = {"execution": "completed", "verdict": "passed", "rows": []}
        self.assertEqual(self.client.post(self.url, {"suite": "ledger-v1"}).status_code, 302)
        run.assert_not_called()
        self.assertEqual(UniversalJob.objects.get().status, 'queued')
        from .universal_queue import process_one
        self.assertTrue(process_one())
        self.assertEqual(AuditEvent.objects.get().organization, self.org)
        self.assertEqual(self.client.get(reverse("studio:universal", args=[self.other.slug])).status_code, 404)

    @patch("studio.universal_queue.execute")
    def test_viewer_cannot_execute(self, run):
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.client.post(self.url, {"suite": "ledger-v1"}).status_code, 403)
        run.assert_not_called()
