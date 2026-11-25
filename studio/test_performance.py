from collections import Counter
from unittest.mock import patch
from django.test import SimpleTestCase
from . import performance as p

class PerformanceTests(SimpleTestCase):
    def test_plan(self):
        self.assertEqual(len(p.plan()), 90)
        self.assertEqual(Counter(c for c,i,n in p.plan()), p.GROUPS)

    def test_parse(self):
        self.assertEqual(p.parse_output("RP_PERF true 10\nGAS: 123", 1), {"valid": True, "gas": 123})

    def test_wrong_state(self):
        self.assertFalse(p.parse_output("RP_PERF true 20", 1)["valid"])

    def test_missing_evidence(self):
        with self.assertRaises(RuntimeError):
            p.parse_output("", 1)

    def test_statistics(self):
        self.assertEqual(p.summarize([1,2,3,4])["p50_ms"], 2.5)
        self.assertEqual(p.summarize([1,2,3,4])["p99_ms"], 4)

    def test_workload(self):
        self.assertIn("i < 200", p.harness_for(200))

    @patch("studio.performance.shutil.which", return_value=None)
    def test_unavailable(self, binary):
        with self.assertRaises(RuntimeError):
            p.run()
