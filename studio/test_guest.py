from django.test import TestCase, Client
from django.urls import reverse
from .models import Membership, Scenario

class GuestTests(TestCase):
    def test_guest_isolation(self):
        self.assertEqual(self.client.get(reverse("studio:public_demo")).status_code, 200)
        self.assertEqual(self.client.get(reverse("studio:guest_start")).status_code, 405)
        response = self.client.post(reverse("studio:guest_start"), {"mode":"developer"})
        self.assertRedirects(response, reverse("studio:dashboard"))
        first = Membership.objects.get(user_id=self.client.session["_auth_user_id"])
        self.assertEqual(Scenario.objects.filter(organization=first.organization).count(), 6)
        other = Client()
        other.post(reverse("studio:guest_start"), {"mode":"review"})
        self.assertEqual(other.get(reverse("studio:organization", args=[first.organization.slug])).status_code, 404)
        self.assertFalse(first.user.has_usable_password())
        self.assertFalse(first.user.is_staff)
