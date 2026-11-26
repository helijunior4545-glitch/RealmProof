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

    def test_guest_launch_feedback_and_isolation(self):
        a, b = self.context(), self.context()
        page = a.new_page()
        page.goto(BASE + "/studio/")
        # Delay only the real POST response, allowing the native pending state to render.
        requests = []
        def delay(route):
            requests.append(route.request.method)
            # Hold navigation without blocking the browser event loop.
            self.pending = route
        page.route("**/studio/guest/start/", delay)
        page.get_by_role("button", name="Launch Hackathon Demo").click(no_wait_after=True)
        expect(page.locator(".jury-launch")).to_have_attribute("aria-busy", "true")
        expect(page.get_by_text("Preparing workspace…", exact=True)).to_be_visible()
        page.locator(".jury-launch").evaluate("(form) => form.requestSubmit(form.querySelector('button'))")
        self.assertEqual(requests, ["POST"])
        page.screenshot(path=str(ART / "guest-pending.png"))
        self.pending.continue_()
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        first = page.url
        other = b.new_page()
        other.goto(BASE + "/studio/")
        other.get_by_role("button", name="Launch Hackathon Demo").click()
        expect(other.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        self.assertNotEqual(first, other.url)
        self.assertEqual(other.goto(first).status, 404)
        page.screenshot(path=str(ART / "workspace.png"), full_page=True)

    def test_landing_responsive_and_keyboard(self):
        for width in (320, 768, 1280, 1920):
            with self.subTest(width=width):
                context = self.context(viewport={"width":width,"height":900}, reduced_motion="reduce")
                page = context.new_page()
                page.goto(BASE + "/studio/")
                expect(page.get_by_role("button", name="Launch Hackathon Demo")).to_be_visible()
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
                page.keyboard.press("Tab")
                expect(page.get_by_role("link", name="Skip to main content")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#main-content")).to_be_focused()
                page.screenshot(path=str(ART / f"landing-{width}.png"), full_page=True)

    def test_native_launch_without_javascript(self):
        page = self.context(java_script_enabled=False).new_page()
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Launch Hackathon Demo").click()
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
