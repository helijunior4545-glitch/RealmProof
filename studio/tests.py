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
