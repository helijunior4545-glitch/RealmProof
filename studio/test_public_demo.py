from django.test import TestCase
from django.urls import reverse

class PublicDemoTests(TestCase):
    def test_anonymous_demo(self):
        url = reverse("studio:public_demo")
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {"balance":100,"amount":150,"authorized":"yes","expected_status":"rejected","expected_balance":100})
        self.assertContains(response, "PASS")
        self.assertContains(response, "Verified on-chain: No")
        self.assertEqual(self.client.get(reverse("studio:dashboard")).status_code, 302)
    def test_invalid_input(self):
        response = self.client.post(reverse("studio:public_demo"), {"balance":-1})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["result"])
