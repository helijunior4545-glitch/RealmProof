"""Public landing UI assertions against Django templates and static assets."""
from django.test import SimpleTestCase
from django.template.loader import get_template
from django.contrib.staticfiles import finders

class PublicExperienceTests(SimpleTestCase):
    def test_landing_explains_verification_without_claiming_chain_proof(self):
        text = get_template("studio/guest_entry.html").template.source
        self.assertIn("Trust the", text)
        self.assertIn("BROWSER ILLUSTRATION", text)
        self.assertIn("ON-CHAIN VERIFIED: NO", text)
        self.assertIn('id="rp-preview"', text)
        self.assertIn('id="rp-trace-expected"', text)
        self.assertIn('id="rp-trace-observed"', text)
        self.assertIn("SOURCE INTELLIGENCE", text)
        self.assertIn("TEST STUDIO", text)
        self.assertIn("EXECUTION CENTER", text)
        self.assertIn("EVIDENCE & REPORTS", text)
        self.assertIn("not affiliated", text.lower())
        self.assertIn("rp-panel-policy", text)
        self.assertIn("rp-panel-diff", text)
        self.assertIn("rp-panel-fingerprint", text)
        self.assertNotIn("onyx.testnets", text)
        self.assertNotIn("lucide", text)

    def test_assets_are_packaged(self):
        self.assertIsNotNone(finders.find("studio/public.css"))
        self.assertIsNotNone(finders.find("studio/public-experience.js"))
        self.assertIsNotNone(finders.find("studio/public-labs.js"))
