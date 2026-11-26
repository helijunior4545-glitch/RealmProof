from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from studio.models import Organization, Membership

class GuestTests(TestCase):
    def test_entry_uses_csrf_post_without_workspace_fields(self):
        client = Client(enforce_csrf_checks=True)
        with patch.dict("os.environ", {"REALMPROOF_ISOLATED_GUESTS": "1"}):
            response = client.get(reverse("studio:public_demo"))
        self.assertContains(response, reverse("studio:guest_start"))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertNotContains(response, 'name="starter"')
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(client.post(reverse("studio:guest_start")).status_code, 403)

    def test_unconfigured(self):
        with patch.dict("os.environ", {"REALMPROOF_DEMO_USERNAME":"","REALMPROOF_DEMO_PASSWORD":""}):
            self.assertContains(self.client.post(reverse("studio:guest_start")), "Guest lab unavailable", status_code=503)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_shared_demo(self):
        user = get_user_model().objects.create_user(username="hackathon_demo_public", password="test-password-123")
        org = Organization.objects.create(name="Demo", slug="review-test")
        Membership.objects.create(user=user, organization=org, role="editor")
        with patch.dict("os.environ", {"REALMPROOF_DEMO_USERNAME":user.username,"REALMPROOF_DEMO_PASSWORD":"test-password-123"}):
            self.assertRedirects(self.client.post(reverse("studio:guest_start")), reverse("studio:organization", args=[org.slug]))
            self.client.logout()
            user.is_staff = True
            user.save()
            self.assertContains(self.client.post(reverse("studio:guest_start")), "Guest lab unavailable", status_code=503)

    def test_guest_session_and_membership_revocation(self):
        user = get_user_model().objects.create_user(username="hackathon_demo_public", password="test-password-123")
        org = Organization.objects.create(name="Demo", slug="review-test")
        Membership.objects.create(user=user, organization=org, role="editor")
        with patch.dict("os.environ", {"REALMPROOF_DEMO_USERNAME":user.username,"REALMPROOF_DEMO_PASSWORD":"test-password-123"}):
            response = self.client.post(reverse("studio:guest_start"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertTrue(self.client.session["realmproof_guest"])
        other = Organization.objects.create(name="Private", slug="private-test")
        Membership.objects.create(user=user, organization=other, role="editor")
        self.assertEqual(self.client.get(reverse("studio:organization", args=[other.slug])).status_code, 404)
        self.assertEqual(self.client.get(reverse("studio:organization", args=[org.slug])).status_code, 404)
