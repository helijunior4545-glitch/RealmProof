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
        with patch("studio.engine.execute", return_value=({"status":"rejected","balance":100,"state_changed":False},{"type":"local_gno","verified_on_chain":False})):
            self.assertEqual(self.client.post(reverse("studio:execute_scenario", args=["demo",scenario.pk])).status_code, 302)
        run = TestRun.objects.get()
        self.assertEqual(run.status, "passed")
        self.assertEqual(run.execution_status, "local_gno")
        self.assertFalse(run.evidence["source"]["verified_on_chain"])

    def test_missing_engine_is_error(self):
        self.client.post(reverse("studio:create_demo", args=["demo"]))
        scenario = Scenario.objects.first()
        with patch("studio.engine.execute", side_effect=RuntimeError("Gno CLI unavailable")):
            self.client.post(reverse("studio:execute_scenario", args=["demo",scenario.pk]))
        self.assertEqual(TestRun.objects.get().status, "error")
