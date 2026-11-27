"""Chromium acceptance against a disposable local Django server."""
import unittest
import os
import shutil
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
        expect(page.get_by_role("heading", name="Test Workbench", exact=True)).to_be_visible()
        first = page.url

        page.goto(BASE + "/studio/")
        page.get_by_role("link", name="Open Project Studio").first.click()
        expect(page).to_have_url(first)

        other = b.new_page()
        other.goto(BASE + "/studio/")
        other.get_by_role("button", name="Open Project Studio").first.click()
        expect(other.get_by_role("heading", name="Test Workbench", exact=True)).to_be_visible()
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
        expect(page.get_by_role("region", name="Scenarios")).to_be_visible()
        expect(page.get_by_role("region", name="Report", exact=True)).to_contain_text("Example · expected values")
        expect(page.get_by_role("region", name="Trace Execution summary", exact=True)).to_contain_text("Transfer(100, 150, true)")
        scenario = page.get_by_role("button", name="Exact balance")
        scenario.click()
        expect(scenario).to_have_attribute("aria-pressed", "true")
        balance = page.get_by_role("row", name="Remaining balance")
        expect(balance.get_by_role("cell").first).to_have_text("0")
        expect(balance.get_by_role("cell").nth(1)).to_have_text("—")
        expect(page.get_by_role("button", name="Run scenario")).to_be_enabled()
        page.get_by_role("button", name="State", exact=True).click()
        expect(page.locator("#lp-report-live")).to_contain_text("Awaiting run")

    def test_example_panels_without_react_bundle(self):
        page = self.context().new_page()
        page.route("**/static/studio/react/landing.js", lambda route: route.abort())
        page.goto(BASE + "/studio/")
        expect(page.get_by_role("heading", name="State comparison")).to_be_visible()
        expect(page.get_by_role("heading", name="Execution report")).to_be_visible()
        report = page.locator("[data-demo-report]")
        report.get_by_role("button", name="Diff").click()
        expect(report.get_by_text("Balance change")).to_be_visible()
        expect(report.get_by_text("Transfer(100, 150, true)")).to_be_hidden()
        expect(page.locator(".lp-invite-panel").get_by_role("button", name="Open Project Studio")).to_be_visible()
        demo = page.locator("#lp-browser-demo")
        demo.get_by_label("Scenario").select_option("valid")
        demo.get_by_role("button", name="Run simulation").click()
        expect(page.locator("#lp-simulation-status")).to_contain_text("Transfer accepted · Test passed · Remaining balance 75")
        demo.get_by_label("Transfer amount").fill("150")
        demo.get_by_role("button", name="Run simulation").click()
        expect(page.locator("#lp-simulation-status")).to_contain_text("Transfer rejected · Test failed · Remaining balance 100")
        expect(page.get_by_role("row", name="Remaining balance")).to_contain_text("Mismatch")
        stages = page.locator("[data-workflow-stages]")
        stages.get_by_role("button", name="Execute").hover()
        expect(stages.get_by_role("heading", name="Execution inputs")).to_be_visible()
        stages.get_by_role("button", name="Observe").focus()
        expect(stages.get_by_role("heading", name="Operation result")).to_be_visible()
        expect(stages.get_by_role("heading", name="State comparison")).to_be_hidden()
        stages.get_by_role("button", name="Compare").click()
        expect(stages.get_by_role("heading", name="State comparison")).to_be_visible()
        expect(report.get_by_text("Test failed")).to_be_visible()
        expect(page.get_by_role("navigation", name="Footer resource links").get_by_role("link", name="GitHub")).to_be_visible()


    def test_native_launch_without_javascript(self):
        page = self.context(java_script_enabled=False).new_page()
        page.goto(BASE + "/studio/")
        expect(page.get_by_role("region", name="Scenarios")).to_be_visible()
        expect(page.get_by_role("region", name="Report", exact=True)).to_be_visible()
        expect(page.get_by_role("region", name="Trace Execution summary", exact=True)).to_be_visible()
        expect(page.get_by_role("radio", name="Insufficient balance")).to_be_checked()
        page.get_by_role("button", name="Open Project Studio").first.click()
        expect(page.get_by_role("heading", name="Test Workbench", exact=True)).to_be_visible()

    @unittest.skipUnless(shutil.which(os.getenv("REALMPROOF_GNO_BINARY", "gno")), "requires the Gno CLI")
    def test_guest_guided_transfer_comparison(self):
        page = self.context().new_page()
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Open Project Studio").first.click()
        expect(page.get_by_role("button", name="Insufficient balance")).to_have_attribute("aria-pressed", "true")
        page.get_by_role("button", name="Run in Gno", exact=True).click()
        expect(page.get_by_text("Transfer rejected", exact=True)).to_be_visible(timeout=25000)
        expect(page.get_by_role("row", name="Remaining balance")).to_contain_text("100")
        page.get_by_role("button", name="Try a valid transfer").click()
        expect(page.get_by_role("heading", name="Compare runs")).to_be_visible(timeout=25000)
        balance = page.get_by_role("row", name="Remaining balance")
        expect(balance.get_by_role("cell").nth(0)).to_have_text("100")
        expect(balance.get_by_role("cell").nth(1)).to_have_text("75")
        expect(page.get_by_role("link", name="Baseline evidence")).to_be_visible()
        expect(page.get_by_role("link", name="Candidate evidence")).to_be_visible()

    @unittest.skipUnless(shutil.which(os.getenv("REALMPROOF_GNO_BINARY", "gno")), "requires the Gno CLI")
    def test_workbench_execution_and_comparison(self):
        page = self.context(viewport={"width": 1440, "height": 920}).new_page()
        page.goto(BASE + "/studio/")
        page.get_by_role("button", name="Open Project Studio").first.click()
        expect(page.get_by_role("heading", name="Test Workbench", exact=True)).to_be_visible()
        page.get_by_role("button", name="Valid transfer").click()
        page.get_by_label("Initial balance").press("Control+Enter")
        expect(page.get_by_text("Runner started", exact=True)).to_be_visible()
        expect(page.get_by_text("Transfer accepted", exact=True)).to_be_visible(timeout=25000)
        expect(page.get_by_role("row", name="Remaining balance")).to_contain_text("75")
        page.get_by_role("button", name="Insufficient balance").click()
        page.get_by_role("button", name="Run scenario").click()
        expect(page.get_by_text("Transfer rejected", exact=True)).to_be_visible(timeout=25000)
        expect(page.get_by_role("row", name="Remaining balance")).to_contain_text("100")
        terminal = page.get_by_role("region", name="Execution terminal")
        expect(terminal.get_by_label("gno-output.txt")).to_contain_text("REALMPROOF_RESULT rejected 100")
        expect(terminal.get_by_text("REALMPROOF_RESULT rejected 100")).to_have_attribute("data-tone", "rejected")
        expect(terminal.get_by_text("--- PASS:", exact=False)).to_have_attribute("data-tone", "pass")
        terminal.get_by_role("button", name="Contract", exact=True).click()
        expect(terminal.get_by_label("transfer.gno")).to_contain_text("func Transfer")
        terminal.get_by_role("button", name="Test harness", exact=True).click()
        expect(terminal.get_by_label("transfer_test.gno")).to_contain_text("Transfer(100, 150, true)")
        terminal.get_by_role("button", name="Run JSON", exact=True).click()
        expect(terminal.get_by_label("run-snapshot.json")).to_contain_text('"source_sha256"')
        terminal.get_by_role("button", name="Expand", exact=True).click()
        expect(terminal.get_by_role("button", name="Restore height")).to_have_attribute("aria-pressed", "true")
        page.get_by_role("button", name="Open in terminal").click()
        expect(terminal.get_by_role("button", name="Terminal Alt Shift T")).to_be_focused()

        page.get_by_role("button", name="Inspect evidence").click()
        expect(page.get_by_role("dialog")).to_contain_text("Report SHA-256")
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).to_be_hidden()
        page.get_by_role("button", name="Compare", exact=True).click()
        expect(page.get_by_role("row", name="Remaining balance")).to_contain_text("Changed")
        page.get_by_role("button", name="History", exact=True).click()
        page.get_by_role("button", name="Refresh runs").click()
        expect(page.get_by_text("Run history updated.")).to_be_visible()
        page.get_by_role("button", name="Suites", exact=True).click()
        expect(page.get_by_role("heading", name="Suites and tools")).to_be_visible()
        page.get_by_role("button", name="Valid transfer").click()
        page.screenshot(path=str(ART / "workbench-desktop.png"), full_page=True)
        page.set_viewport_size({"width": 360, "height": 780})
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
        page.screenshot(path=str(ART / "workbench-mobile.png"), full_page=True)
