from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Organization, Membership, Project

class ReviewTests(TestCase):
    def test_share_is_read_only_and_tenant_scoped(self):
        user = get_user_model().objects.create_user(username="publisher")
        org = Organization.objects.create(name="Publisher", slug="publisher")
        other = Organization.objects.create(name="Other", slug="other")
        Membership.objects.create(user=user, organization=org, role="owner")
        project = Project.objects.create(organization=org, name="Review project")
        foreign = Project.objects.create(organization=other, name="Private project")
        self.client.force_login(user)
        self.assertEqual(self.client.post(reverse("studio:publish_review", args=[org.slug, foreign.pk])).status_code,404)
        url = reverse("studio:publish_review", args=[org.slug, project.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        response = self.client.post(url)
        self.assertEqual(response.status_code,200)
        link = response.context["link"]
        self.client.logout()
        from urllib.parse import urlsplit
        path = urlsplit(link).path
        self.assertContains(self.client.get(path),"Review project")
        self.assertEqual(self.client.post(path).status_code,405)
        self.assertEqual(self.client.get(path.rstrip("/")+"x/").status_code,404)
