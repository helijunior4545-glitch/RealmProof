"""The public landing explains the product and links directly to the real lab."""
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.test import SimpleTestCase


class PublicExperienceTests(SimpleTestCase):
    def test_entry_has_native_start_without_marketing_or_signup(self):
        template = get_template("studio/guest_entry.html")
        page = template.render({"guest_enabled": True, "csrf_token": "token"})
        self.assertIn('method="post"', page)
        self.assertIn("Open Studio as guest", page)
        self.assertNotIn("Create workspace", page)
        self.assertIn("Test Gno contracts.", page)
        self.assertIn("BROWSER ILLUSTRATION", page)

    def test_entry_assets_are_packaged(self):
        for asset in ("public.css", "public-experience.js", "public-labs.js"):
            self.assertIsNotNone(finders.find(f"studio/{asset}"))
