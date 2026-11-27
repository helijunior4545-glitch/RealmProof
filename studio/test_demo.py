import hashlib
import json
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Organization, Membership, Scenario, TestRun

class DemoExecutionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="demo")
        self.org = Organization.objects.create(name="Demo", slug="demo")
        Membership.objects.create(user=self.user, organization=self.org, role="owner")
        self.client.force_login(self.user)

    def test_demo_and_execution_pipeline(self):
        self.assertEqual(self.client.post(reverse("studio:create_demo", args=["demo"])).status_code, 302)
        self.assertEqual(Scenario.objects.count(), 6)
        scenario = Scenario.objects.get(name="Insufficient balance")
        with patch("studio.engine.execute", return_value=({"status":"rejected","balance":100,"state_changed":False},{"type":"local_gno","verified_on_chain":False,"source_sha256":"a"*64,"harness_sha256":"b"*64})):
            self.assertEqual(self.client.post(reverse("studio:execute_scenario", args=["demo",scenario.pk])).status_code, 302)
        run = TestRun.objects.get()
        self.assertEqual(run.status, "passed")
        self.assertEqual(run.execution_status, "local_gno")
        self.assertFalse(run.evidence["source"]["verified_on_chain"])
        report = self.client.get(reverse("studio:run_detail", args=["demo", run.pk]))
        self.assertContains(report, "Transfer rejected")
        self.assertContains(report, "Test passed")
        self.assertContains(report, "3 of 3 assertions matched.")
        self.assertContains(report, "Remaining balance")
        self.assertNotContains(report, "Duration")
        export = reverse("studio:download_run_evidence", args=["demo", run.pk])
        response = self.client.get(export)
        digest = hashlib.sha256(response.content).hexdigest()
        self.assertEqual(response.status_code, 200)
        self.assertContains(report, digest)
        self.assertEqual(json.loads(response.content)["observed"]["balance"], 100)
        self.assertEqual(self.client.get(export).content, response.content)
        self.client.force_login(get_user_model().objects.create_user(username="external"))
        self.assertEqual(self.client.get(export).status_code, 404)

    def test_missing_engine_is_error(self):
        self.client.post(reverse("studio:create_demo", args=["demo"]))
        scenario = Scenario.objects.first()
        with patch("studio.engine.execute", side_effect=RuntimeError("Gno CLI unavailable")):
            self.client.post(reverse("studio:execute_scenario", args=["demo",scenario.pk]))
        run = TestRun.objects.get()
        self.assertEqual(run.status, "error")
        report = self.client.get(reverse("studio:run_detail", args=["demo", run.pk]))
        self.assertContains(report, "Infrastructure error")
        self.assertContains(report, "Gno CLI unavailable")
        self.assertNotContains(report, "MISMATCH")
        self.assertEqual(self.client.get(reverse("studio:download_run_evidence", args=["demo", run.pk])).status_code, 404)
