from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from studio.models import Organization, Membership

class SharedDemoBoundaryTests(TestCase):
    def test_demo_cannot_create_another_tenant(self):
        user = get_user_model().objects.create_user(username="hackathon_demo_public")
        org = Organization.objects.create(name="Demo", slug="review-demo")
        Membership.objects.create(user=user, organization=org, role="editor")
        self.client.force_login(user)
        self.assertEqual(self.client.post(reverse("studio:create_organization"), {"name":"Other","slug":"other"}).status_code, 403)
        self.assertEqual(Membership.objects.filter(user=user).count(), 1)
