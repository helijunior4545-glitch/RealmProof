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
        # The UI intentionally paints for two animation frames before native navigation.
        # Await the actual request instead of asserting against the event loop prematurely.
        with page.expect_request("**/studio/guest/start/") as submitted:
            page.get_by_role("button", name="Create Workspace").click(no_wait_after=True)
            expect(page.locator(".jury-launch")).to_have_attribute("aria-busy", "true")
            expect(page.get_by_text("Preparing workspace…", exact=True)).to_be_visible()
            page.locator(".jury-launch").evaluate("(form) => form.requestSubmit(form.querySelector('button'))")
        self.assertEqual(submitted.value.method, "POST")
        self.assertEqual(requests, ["POST"])
        # Playwright screenshots wait for navigations; keep the pending-state assertions
        # above and capture the settled workspace after releasing the held request.
        self.pending.continue_()
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
        first = page.url
        other = b.new_page()
        other.goto(BASE + "/studio/")
        other.get_by_role("button", name="Create Workspace").click()
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
                expect(page.get_by_role("button", name="Create Workspace")).to_be_visible()
                self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
                page.keyboard.press("Tab")
                expect(page.get_by_role("link", name="Skip to main content")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#main-content")).to_be_focused()
                page.screenshot(path=str(ART / f"landing-{width}.png"), full_page=True)

    def test_verification_model_interactive_and_honest(self):
        page = self.context().new_page()
        page.goto(BASE + "/studio/")
        page.locator('[data-case="funds"]').click()
        expect(page.locator("#rp-trace-expected")).to_contain_text("status=insufficient_funds")
        expect(page.locator("#rp-trace-observed")).to_contain_text("Select")
        page.locator("#rp-preview").click()
        expect(page.locator("#rp-trace-observed")).to_contain_text("status=insufficient_funds")
        expect(page.locator("#rp-preview-status")).to_contain_text("MODEL PREVIEW MATCHES EXPECTED")
        expect(page.get_by_text("ON-CHAIN VERIFIED: NO")).to_be_visible()
        page.locator('[data-case="permission"]').click()
        expect(page.locator("#rp-trace-expected")).to_contain_text("status=permission_denied")
        expect(page.locator("#rp-trace-observed")).to_contain_text("Select")
        page.locator(".rp-toggle").click()
        expect(page.locator("#rp-trace-expected")).to_contain_text("status=ok")
        page.locator("#rp-amount").fill("-1")
        expect(page.locator("#rp-preview")).to_be_disabled()
        page.screenshot(path=str(ART / "verification-inspector.png"), full_page=True)


    def test_interactive_engineering_desk_and_mismatch(self):
        import re
        page = self.context(reduced_motion="reduce").new_page()
        page.goto(BASE + "/studio/")
        page.locator("#rp-expect-status").select_option("permission_denied")
        page.locator("#rp-preview").click()
        expect(page.locator("#rp-preview-status")).to_contain_text("DIFFERS FROM EXPECTED")
        page.get_by_role("tab", name="Permission policy").click()
        page.locator("#rp-policy-role").select_option("viewer")
        page.locator("#rp-policy-action").select_option("publish")
        page.locator("#rp-policy-run").click()
        expect(page.locator("#rp-policy-verdict")).to_contain_text("DENY")
        page.get_by_role("tab", name="Source comparison").click()
        page.locator("#rp-diff-run").click()
        expect(page.locator("#rp-diff-count")).to_contain_text("1 ADDED")
        expect(page.locator(".rp-diff-remove")).to_contain_text("authorized &&")
        page.get_by_role("tab", name="Evidence fingerprint").click()
        page.locator("#rp-fingerprint-run").click()
        expect(page.locator("#rp-fingerprint-status")).to_contain_text("DIGESTS DIFFER")
        self.assertRegex(page.locator("#rp-fingerprint-hash-a").inner_text(), r"^[a-f0-9]{64}$")
        page.locator("#rp-fingerprint-b").fill(page.locator("#rp-fingerprint-a").input_value())
        page.locator("#rp-fingerprint-run").click()
        expect(page.locator("#rp-fingerprint-status")).to_contain_text("DIGESTS MATCH")
        page.screenshot(path=str(ART / "engineering-desk.png"), full_page=True)

    def test_native_launch_without_javascript(self):
        page = self.context(java_script_enabled=False).new_page()
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Create Workspace").click()
        expect(page.get_by_role("heading", name="Transfer verification lab", exact=True)).to_be_visible()
