from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Organization, Membership, Project, Scenario
from .guest_provisioning import PREFIX

class IsolatedGuestTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="hackathon_demo_public", password="test-password-123")
        org = Organization.objects.create(name="Template", slug="review-template")
        Membership.objects.create(user=user, organization=org, role="editor")

    def launch(self, client):
        with patch.dict("os.environ", {"REALMPROOF_ISOLATED_GUESTS":"1","REALMPROOF_DEMO_USERNAME":"hackathon_demo_public","REALMPROOF_DEMO_PASSWORD":"test-password-123"}):
            return client.post(reverse("studio:guest_start"))

    def test_independent_visitors(self):
        a, b = Client(), Client()
        first, second = self.launch(a), self.launch(b)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertNotEqual(first.url, second.url)
        self.assertEqual(a.get(second.url).status_code, 404)
        self.assertEqual(b.get(first.url).status_code, 404)
        self.assertEqual(a.get(first.url).status_code, 200)
        self.assertEqual(Scenario.objects.count(), 12)
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(a.post(reverse("studio:create_organization"), {"name":"Other","slug":"other"}).status_code, 403)
        self.assertTrue(all(not u.has_usable_password() for u in get_user_model().objects.filter(username__startswith=PREFIX)))

    def test_capacity_fails_closed(self):
        with patch("studio.guest_provisioning.CAP", 0):
            response = self.launch(self.client)
        self.assertRedirects(response, reverse("studio:public_demo"))
        self.assertFalse(get_user_model().objects.filter(username__startswith=PREFIX).exists())
