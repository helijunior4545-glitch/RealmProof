"""Chromium acceptance against a disposable local Django server."""
import unittest
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://127.0.0.1:8765"
ART = Path("browser-artifacts")


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ART.mkdir(exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def page(self, **kwargs):
        context = self.browser.new_context(**kwargs)
        self.addCleanup(context.close)
        return context.new_page()

    def expect_lab(self, page):
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Execute Gno")).to_have_count(6)

    def test_auto_entry_and_guest_isolation(self):
        first, second = self.page(), self.page()
        with first.expect_request("**/studio/guest/start/") as submitted:
            first.goto(BASE + "/")
        self.assertEqual(submitted.value.method, "POST")
        self.expect_lab(first)
        original = first.url

        first.goto(BASE + "/studio/")
        self.expect_lab(first)
        self.assertEqual(first.url, original)

        second.goto(BASE + "/studio/test/")
        self.expect_lab(second)
        self.assertNotEqual(first.url, second.url)
        self.assertEqual(second.goto(first.url).status, 404)

    def test_project_responsive_and_keyboard(self):
        for width in (320, 768, 1366):
            with self.subTest(width=width):
                page = self.page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
                page.goto(BASE + "/studio/")
                self.expect_lab(page)
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
                page.keyboard.press("Tab")
                expect(page.get_by_role("link", name="Skip to main content")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#main-content")).to_be_focused()
                expect(page.locator(".scenario-row").first.get_by_role("heading")).to_have_text("Valid transfer")
                page.screenshot(path=str(ART / f"workspace-{width}.png"), full_page=True)

    def test_native_entry_without_javascript(self):
        page = self.page(java_script_enabled=False)
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Open transfer lab").click()
        self.expect_lab(page)
