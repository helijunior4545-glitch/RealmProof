from django.test import SimpleTestCase
from .test_intelligence import RULES, recommend

class RecommendationTests(SimpleTestCase):
    def test_all_rules_and_no_inferred_expected(self):
        indicators = [{"rule": rule, "function": "A", "line": 2} for rule in RULES]
        result = recommend({"status": "parsed", "indicators": indicators})
        self.assertEqual(len(result["items"]), 5)
        self.assertFalse(result["partial"])
        for item in result["items"]:
            self.assertIsNone(item["expected"])
            self.assertEqual(item["status"], "proposed")
            self.assertTrue(item["oracle"])

    def test_unavailable_and_empty(self):
        self.assertEqual(recommend({"status": "syntax_error"})["status"], "unavailable")
        self.assertEqual(recommend({"status": "parsed"})["status"], "unavailable")
        self.assertEqual(recommend({"status": "parsed", "indicators": []})["items"], [])

    def test_deduplication_and_cap(self):
        indicators = [{"rule": "index_boundary", "function": "A", "line": i} for i in range(101)]
        result = recommend({"status": "parsed", "indicators": [indicators[0]] + indicators})
        self.assertEqual(len(result["items"]), 100)
        self.assertTrue(result["partial"])

    def test_incomplete_input(self):
        self.assertTrue(recommend({"status": "parsed", "indicators": [], "indicators_truncated": True})["partial"])
        self.assertTrue(recommend({"status": "parsed", "indicators": [{"rule": "unknown"}]})["partial"])
