from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class GuestTests(TestCase):
    def test_public_entry_does_not_create_accounts(self):
        self.assertEqual(self.client.get(reverse("studio:public_demo")).status_code, 200)
        self.assertEqual(self.client.get(reverse("studio:guest_start")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("studio:guest_start")), reverse("login"))
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(self.client.get(reverse("studio:dashboard")).status_code, 302)
