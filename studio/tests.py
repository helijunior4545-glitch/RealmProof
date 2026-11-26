from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import Organization, Membership, Project, Scenario, TestRun
from .services import evaluate


class AssertionTests(TestCase):
    def test_passed_when_expected_subset_matches(self):
        self.assertEqual(evaluate({"status": "reverted"}, {"status": "reverted", "height": 12}).status, "passed")

    def test_failed_when_expected_differs(self):
        result = evaluate({"balance": 10}, {"balance": 12})
        self.assertEqual(result.status, "failed")
        self.assertIn("balance", result.evidence["mismatches"])

    def test_inconclusive_without_expected_assertions(self):
        self.assertEqual(evaluate({}, {"status": "ok"}).status, "inconclusive")

    def test_missing_field_fails(self):
        self.assertEqual(evaluate({"status": "ok"}, {}).status, "failed")


class TenancyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", password="secure-example-a")
        self.bob = User.objects.create_user(username="bob", password="secure-example-b")
        self.a = Organization.objects.create(name="Alpha", slug="alpha")
        self.b = Organization.objects.create(name="Beta", slug="beta")
        Membership.objects.create(organization=self.a, user=self.alice, role="owner")
        Membership.objects.create(organization=self.b, user=self.bob, role="owner")
        self.p = Project.objects.create(organization=self.a, name="Alpha project")
        self.s = Scenario.objects.create(
            organization=self.a, project=self.p, name="State unchanged", objective="Check unchanged state",
            input_data={"amount": 20}, expected={"balance": 10},
        )

    def test_another_tenant_cannot_open_project(self):
        self.client.force_login(self.bob)
        url = reverse("studio:project", args=["beta", self.p.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_another_tenant_cannot_run_scenario(self):
        self.client.force_login(self.bob)
        url = reverse("studio:start_run", args=["beta", self.s.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(TestRun.objects.count(), 0)

    def test_unauthenticated_user_redirected(self):
        self.assertEqual(self.client.get(reverse("studio:dashboard")).status_code, 302)

    def test_no_get_mutations(self):
        self.client.force_login(self.alice)
        url = reverse("studio:start_run", args=["alpha", self.s.pk])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_create_run_is_pending_and_does_not_fake_chain_proof(self):
        self.client.force_login(self.alice)
        url = reverse("studio:start_run", args=["alpha", self.s.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        run = TestRun.objects.get()
        self.assertEqual(run.status, "pending")
        self.assertEqual(run.execution_status, "not_executed")

    def test_viewer_cannot_evaluate(self):
        Membership.objects.filter(organization=self.a, user=self.alice).update(role="viewer")
        self.client.force_login(self.alice)
        self.assertEqual(self.client.post(reverse("studio:start_run", args=["alpha", self.s.pk])).status_code, 403)

    def test_scenario_rejects_cross_organization_project(self):
        other = Scenario(organization=self.b, project=self.p, name="Bad", objective="Invalid relation")
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            other.save()

    def test_user_supplied_evidence_explicitly_not_verified_on_chain(self):
        self.client.force_login(self.alice)
        self.client.post(reverse("studio:start_run", args=["alpha", self.s.pk]))
        run = TestRun.objects.get()
        url = reverse("studio:evaluate_run", args=["alpha", run.pk])
        self.assertEqual(self.client.post(url, {"observed": '{"balance":10}'}).status_code, 302)
        run.refresh_from_db()
        self.assertEqual(run.status, "passed")
        self.assertFalse(run.evidence["source"]["verified_on_chain"])
        self.assertEqual(self.client.post(url, {"observed": '{"balance":999}'}).status_code, 302)
        run.refresh_from_db()
        self.assertEqual(run.observed["balance"], 10)


class ConsoleFlowTests(TestCase):
    """Protect the user journey, tenant boundaries, and truthful evidence labels."""

    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="console-owner", password="test-password-123")
        self.outsider = User.objects.create_user(username="console-outsider", password="test-password-123")
        self.org = Organization.objects.create(name="Console Labs", slug="console-labs")
        self.other = Organization.objects.create(name="Outside", slug="outside-labs")
        Membership.objects.create(organization=self.org, user=self.owner, role="owner")
        Membership.objects.create(organization=self.other, user=self.outsider, role="owner")
        self.project = Project.objects.create(organization=self.org, name="Treasury")
        self.scenario = Scenario.objects.create(
            organization=self.org, project=self.project, name="Reject overspend",
            family="invalid", objective="Transfer above balance should revert",
            input_data={"balance": 100, "amount": 150},
            expected={"status": "reverted", "balance": 100},
        )
        self.client.force_login(self.owner)

    def test_dashboard_describes_intent_and_local_scope(self):
        response = self.client.get(reverse("studio:dashboard"))
        self.assertContains(response, "Build confidence in every contract.")
        self.assertContains(response, "No chain connected")
        self.assertContains(response, 'name="viewport"')

    def test_project_workbench_shows_scenario_and_environment_boundary(self):
        response = self.client.get(reverse("studio:project", args=[self.org.slug, self.project.pk]))
        self.assertContains(response, "TESTING WORKBENCH")
        self.assertContains(response, self.scenario.name)
        self.assertContains(response, "Not connected")
        self.assertContains(response, "Recent runs")

    def test_scenario_builder_has_three_steps_and_templates(self):
        response = self.client.get(reverse("studio:create_scenario", args=[self.org.slug, self.project.pk]))
        self.assertContains(response, "Start with intent.")
        self.assertContains(response, 'data-step-panel="0"')
        self.assertContains(response, 'data-step-panel="1"')
        self.assertContains(response, 'data-step-panel="2"')
        self.assertContains(response, 'data-preset="insufficient"')

    def test_scenario_builder_persists_expected_outcome(self):
        import json
        response = self.client.post(
            reverse("studio:create_scenario", args=[self.org.slug, self.project.pk]),
            {
                "name": "New failure case",
                "family": "invalid",
                "objective": "Expected contract rejection",
                "input_data": json.dumps({"amount": 999}),
                "expected": json.dumps({"status": "reverted"}),
            },
        )
        self.assertEqual(response.status_code, 302)
        scenario = Scenario.objects.get(name="New failure case")
        self.assertEqual(scenario.expected, {"status": "reverted"})
        self.assertEqual(scenario.organization, self.org)

    def test_run_console_separates_verdict_from_execution(self):
        response = self.client.post(reverse("studio:start_run", args=[self.org.slug, self.scenario.pk]))
        self.assertEqual(response.status_code, 302)
        run = TestRun.objects.get()
        response = self.client.get(reverse("studio:run_detail", args=[self.org.slug, run.pk]))
        self.assertContains(response, "ASSERTION VERDICT")
        self.assertContains(response, "Not executed")
        self.assertContains(response, "does not currently submit transactions")
        self.client.post(
            reverse("studio:evaluate_run", args=[self.org.slug, run.pk]),
            {"observed": '{"status":"reverted","balance":100}'},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, "passed")
        response = self.client.get(reverse("studio:run_detail", args=[self.org.slug, run.pk]))
        self.assertContains(response, "User supplied")
        self.assertContains(response, "unverified")
        self.assertContains(response, "MATCH")
        self.assertContains(response, "Raw technical evidence")

    def test_failed_assertion_is_explained_as_mismatch(self):
        self.client.post(reverse("studio:start_run", args=[self.org.slug, self.scenario.pk]))
        run = TestRun.objects.get()
        self.client.post(
            reverse("studio:evaluate_run", args=[self.org.slug, run.pk]),
            {"observed": '{"status":"success","balance":0}'},
        )
        response = self.client.get(reverse("studio:run_detail", args=[self.org.slug, run.pk]))
        self.assertContains(response, "MISMATCH")
        self.assertContains(response, "FAILED")

    def test_unrelated_tenant_cannot_open_console_run(self):
        self.client.post(reverse("studio:start_run", args=[self.org.slug, self.scenario.pk]))
        run = TestRun.objects.get()
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("studio:run_detail", args=[self.other.slug, run.pk]))
        self.assertEqual(response.status_code, 404)
