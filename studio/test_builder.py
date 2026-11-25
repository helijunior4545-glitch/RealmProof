from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Organization, Membership, Scenario

class BuilderTests(TestCase):
    def test_custom_demo(self):
        user=get_user_model().objects.create_user(username="builder")
        org=Organization.objects.create(name="Builder",slug="builder")
        Membership.objects.create(user=user,organization=org,role="owner")
        self.client.force_login(user)
        url=reverse("studio:demo_builder",args=[org.slug])
        self.assertEqual(self.client.get(url).status_code,200)
        response=self.client.post(url,{"title":"Custom","description":"Demo","scenario":"Reject","objective":"Preserve balance","balance":100,"amount":150,"authorized":"yes","expected_status":"rejected","expected_balance":100,"expected_change":"no"})
        self.assertEqual(response.status_code,302)
        scenario=Scenario.objects.get(organization=org)
        self.assertEqual(scenario.input_data["amount"],150)
        self.assertFalse(scenario.expected["state_changed"])
