from django.test import SimpleTestCase
from .specialized import campaign, harness_for, parse_output, SPECS
from .universal import SUITES

class CampaignTests(SimpleTestCase):
    def test_counts_and_reproducibility(self):
        for kind, (count, _) in SPECS.items():
            self.assertEqual(len(campaign(kind)), count)
            self.assertEqual(campaign(kind), campaign(kind))
            self.assertEqual(SUITES[kind+"-v1"].checks, count)

    def test_reset_before_each_case(self):
        for kind in SPECS:
            cases = campaign(kind)
            self.assertTrue(all(c["setup"][:4] == ["available = 0", "held = 0", "paid = 0", "frozen = false"] for c in cases))

    def test_parser_preserves_false(self):
        cases = campaign("integration")[:2]
        self.assertEqual(parse_output("RP_CASE 0 true\nRP_CASE 1 false\n", cases), [True, False])

    def test_parser_rejects_missing_or_duplicate(self):
        cases = campaign("integration")[:2]
        for output in ["RP_CASE 0 true", "RP_CASE 0 true\nRP_CASE 0 false"]:
            with self.assertRaises(RuntimeError):
                parse_output(output, cases)

    def test_harness_contains_all_cases(self):
        cases = campaign("fuzz")[:50]
        self.assertEqual(harness_for(cases).count("fmt.Println"), 50)
