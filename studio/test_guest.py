from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from studio.models import Organization, Membership

class GuestTests(TestCase):
    def test_unconfigured(self):
        with patch.dict("os.environ", {"REALMPROOF_DEMO_USERNAME":"","REALMPROOF_DEMO_PASSWORD":""}):
            self.assertRedirects(self.client.post(reverse("studio:guest_start")), reverse("studio:public_demo"))
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
            self.assertRedirects(self.client.post(reverse("studio:guest_start")), reverse("studio:public_demo"))
