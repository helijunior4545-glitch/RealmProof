"""The public entry delivers the real lab rather than an illustrative page."""
from django.contrib.staticfiles import finders
from django.template.loader import get_template
from django.test import SimpleTestCase


class PublicExperienceTests(SimpleTestCase):
    def test_entry_has_native_start_without_marketing_or_signup(self):
        template = get_template("studio/guest_entry.html")
        page = template.render({"auto_start": True, "csrf_token": "token"})
        self.assertIn('method="post"', page)
        self.assertIn("Open transfer lab", page)
        self.assertNotIn("Create workspace", page)
        self.assertNotIn("Verify smart contracts", page)

    def test_entry_assets_are_packaged(self):
        for asset in ("guest-entry.js", "entry.css", "project-workbench.css"):
            self.assertIsNotNone(finders.find(f"studio/{asset}"))
