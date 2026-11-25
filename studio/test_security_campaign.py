from collections import Counter
from unittest.mock import patch
from django.test import SimpleTestCase
from . import security_campaign as security
from .universal import SUITES

class SecurityCampaignTests(SimpleTestCase):
    def test_distribution(self):
        cases = security.campaign()
        self.assertEqual(len(cases), 600)
        self.assertEqual(Counter(c["input"]["category"] for c in cases), security.GROUPS)
        self.assertEqual([c["id"] for c in cases], list(range(600)))

    def test_reproducible(self):
        self.assertEqual(security.campaign(), security.campaign())

    def test_every_step_is_checked(self):
        for case in security.campaign():
            self.assertEqual(sum(s.startswith("valid =") for s in case["setup"]), len(case["input"]["operations"]))

    def test_registry(self):
        self.assertEqual(SUITES["security-v1"].checks, 600)

    @patch("studio.security_campaign.run_cases")
    def test_adapter(self, runner):
        security.run()
        self.assertEqual(runner.call_args.kwargs["seed"], security.SEED)
        self.assertEqual(len(runner.call_args.kwargs["cases"]), 600)
