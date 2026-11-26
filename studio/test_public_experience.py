from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase
from django.urls import reverse


class PublicExperienceTests(SimpleTestCase):
    def test_landing_explains_the_workflow_and_offers_direct_guest_access(self):
        with patch.dict("os.environ", {"REALMPROOF_ISOLATED_GUESTS": "1"}):
            response = self.client.get(reverse("studio:public_demo"))
        self.assertContains(response, "Open Project Studio")
        self.assertContains(response, "From scenario to evidence")
        self.assertContains(response, "Local Gno")
        self.assertContains(response, reverse("studio:guest_preview"))
        self.assertContains(response, 'id="lp-scenarios"')
        self.assertNotContains(response, "Create workspace")
        self.assertIsNotNone(finders.find("studio/guest-landing.css"))

    @patch.dict("os.environ", {"REALMPROOF_ISOLATED_GUESTS": "1"})
    def test_preview_runs_only_the_selected_fixture_and_evaluates_observed_values(self):
        url = reverse("studio:guest_preview")
        with patch("studio.guest.engine.execute") as execute:
            self.assertEqual(self.client.post(url, {"scenario": "unknown"}).status_code, 400)
            execute.assert_not_called()
            execute.return_value = (
                {"status": "rejected", "balance": 100, "state_changed": False},
                {"duration_ms": 21, "source_sha256": "a" * 64, "harness_sha256": "b" * 64},
            )
            result = self.client.post(url, {"scenario": "insufficient", "amount": 1}).json()
            execute.assert_called_once_with({"balance": 100, "amount": 150, "authorized": True})
        self.assertEqual(result["verdict"], "passed")
        self.assertEqual(result["observed"]["status"], "rejected")
        self.assertFalse(result["mismatches"])

    def test_preview_requires_post_csrf_and_isolated_guest_mode(self):
        url = reverse("studio:guest_preview")
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.get(url).status_code, 405)
        self.assertEqual(client.post(url, {"scenario": "valid"}).status_code, 403)
        with patch.dict("os.environ", {"REALMPROOF_ISOLATED_GUESTS": "0"}):
            self.assertEqual(self.client.post(url, {"scenario": "valid"}).status_code, 503)
