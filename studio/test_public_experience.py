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

    def test_studio_entry_uses_authorized_destination_or_guest_post(self):
        text = get_template("studio/guest_entry.html").template.source
        self.assertIn('href="{{ studio_url }}"', text)
        self.assertIn('action="{% url \'studio:guest_start\' %}"', text)
        self.assertIn("Open Project Studio", text)
        self.assertNotIn("guest-4ef1e5083a884008931495d2bc813082", text)

    def test_assets_are_packaged(self):
        self.assertIsNotNone(finders.find("studio/capabilities.css"))
        self.assertIsNotNone(finders.find("studio/public-capabilities.js"))
        self.assertIsNotNone(finders.find("studio/public.css"))
        self.assertIsNotNone(finders.find("studio/public-experience.js"))
        self.assertIsNotNone(finders.find("studio/public-labs.js"))
        self.assertIsNotNone(finders.find("studio/hero-project-studio.svg"))
