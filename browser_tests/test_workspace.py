"""Chromium acceptance against a disposable local Django server."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

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

    def context(self, **kwargs):
        context = self.browser.new_context(**kwargs)
        self.addCleanup(context.close)
        return context

    def test_guest_launch_and_isolation(self):
        a, b = self.context(), self.context()
        page = a.new_page()
        page.goto(BASE + "/studio/")
        expect(page.locator("form.jury-launch input:not([type=hidden]), form.jury-launch textarea, form.jury-launch select")).to_have_count(0)
        with page.expect_request("**/studio/guest/start/") as submitted:
            page.get_by_role("button", name="Open Project Studio").first.click()
        self.assertEqual(submitted.value.method, "POST")
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        first = page.url

        page.goto(BASE + "/studio/")
        page.get_by_role("link", name="Open Project Studio").first.click()
        expect(page).to_have_url(first)

        other = b.new_page()
        other.goto(BASE + "/studio/")
        other.get_by_role("button", name="Open Project Studio").first.click()
        expect(other.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        self.assertNotEqual(first, other.url)
        self.assertEqual(other.goto(first).status, 404)
        page.screenshot(path=str(ART / "workspace.png"), full_page=True)

    def test_landing_responsive_and_keyboard(self):
        for width in (320, 768, 1280, 1366, 1920):
            with self.subTest(width=width):
                context = self.context(viewport={"width":width,"height":900}, reduced_motion="reduce")
                page = context.new_page()
                page.goto(BASE + "/studio/")
                expect(page.locator(".lp-hero").get_by_role("button", name="Open Project Studio")).to_be_visible()
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
                page.keyboard.press("Tab")
                expect(page.get_by_role("link", name="Skip to main content")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#main-content")).to_be_focused()
                expect(page.get_by_role("heading", name="Transfer lab", exact=True)).to_be_visible()
                expect(page.get_by_role("contentinfo")).to_be_visible()
                page.screenshot(path=str(ART / f"landing-{width}.png"), full_page=True)

    def test_landing_scenario_selection_and_expected_values(self):
        page = self.context().new_page()
        page.goto(BASE + "/studio/")
        scenario = page.get_by_role("button", name="Exact balance")
        scenario.click()
        expect(scenario).to_have_attribute("aria-pressed", "true")
        balance = page.get_by_role("row", name="Remaining balance")
        expect(balance.get_by_role("cell").first).to_have_text("0")
        expect(balance.get_by_role("cell").nth(1)).to_have_text("—")
        expect(page.get_by_role("button", name="Run scenario")).to_be_enabled()

    def test_native_launch_without_javascript(self):
        page = self.context(java_script_enabled=False).new_page()
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Open Project Studio").first.click()
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
