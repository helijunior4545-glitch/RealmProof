"""Public landing UI assertions against Django templates and static assets."""
from django.test import SimpleTestCase
from django.template.loader import get_template
from django.contrib.staticfiles import finders

class PublicExperienceTests(SimpleTestCase):
    def test_landing_explains_verification_without_claiming_chain_proof(self):
        text = get_template("studio/guest_entry.html").template.source
        self.assertIn("Verify smart contracts", text)
        self.assertIn("hero-project-studio.svg", text)
        self.assertIn("Static schematic, not live evidence", text)
        self.assertIn("BROWSER ILLUSTRATION", text)
        self.assertIn("ON-CHAIN VERIFIED: NO", text)
        self.assertIn('id="rp-preview"', text)
        self.assertIn('id="rp-trace-expected"', text)
        self.assertIn('id="rp-trace-observed"', text)
        self.assertIn("source intelligence", text.lower())
        self.assertIn("test studio", text.lower())
        self.assertIn("execution center", text.lower())
        self.assertIn("evidence & reports", text.lower())
        self.assertIn("not affiliated", text.lower())
        self.assertIn("rp-panel-policy", text)
        self.assertIn("rp-panel-diff", text)
        self.assertIn("rp-panel-fingerprint", text)
        self.assertNotIn("onyx.testnets", text)
        self.assertNotIn("lucide", text)

    def test_capability_workflow_previews(self):
        source = get_template("studio/guest_entry.html").template.source
        self.assertEqual(source.count('class="rp-cap-preview"'), 5)
        self.assertEqual(source.count('class="rp-cap-step"'), 15)
        self.assertEqual(source.count("WORKFLOW PREVIEW · SAMPLE"), 5)
        for accent in ("#70c9ff", "#c2a2ff", "#67e3b1", "#f5bb71", "#62ded5"):
            self.assertIn(accent, source)

    def test_assets_are_packaged(self):
        self.assertIsNotNone(finders.find("studio/capabilities.css"))
        self.assertIsNotNone(finders.find("studio/public-capabilities.js"))
        self.assertIsNotNone(finders.find("studio/public.css"))
        self.assertIsNotNone(finders.find("studio/public-experience.js"))
        self.assertIsNotNone(finders.find("studio/public-labs.js"))
        self.assertIsNotNone(finders.find("studio/hero-project-studio.svg"))


from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class InternalEngineeringRoutingTests(TestCase):
    def test_public_entry_does_not_expose_internal_lab(self):
        response = self.client.get(reverse("studio:public_demo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verify smart contracts.")
        self.assertNotContains(response, "INTERACTIVE VERIFICATION MODEL")
        self.assertNotContains(response, "rp-panel-policy")

    def test_internal_lab_requires_login(self):
        response = self.client.get(reverse("studio:engineering_lab"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_internal_lab_preserves_all_tools_and_truthful_labels(self):
        user = get_user_model().objects.create_user(username="engineering-tester", password="example-credential")
        self.client.force_login(user)
        response = self.client.get(reverse("studio:engineering_lab"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INTERACTIVE VERIFICATION MODEL")
        self.assertContains(response, "ON-CHAIN VERIFIED: NO")
        self.assertContains(response, "rp-panel-policy")
        self.assertContains(response, "rp-panel-diff")
        self.assertContains(response, "rp-panel-fingerprint")
