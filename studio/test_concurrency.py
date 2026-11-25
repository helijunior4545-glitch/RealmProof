from collections import Counter
from unittest.mock import patch
from django.test import SimpleTestCase
from . import concurrency

class ConcurrencyTests(SimpleTestCase):
    def test_plan(self):
        self.assertEqual(len(concurrency.plan()), 300)
        self.assertEqual(Counter(g for g,i,a in concurrency.plan()), concurrency.GROUPS)

    def test_reproducibility(self):
        self.assertEqual(concurrency.plan(), concurrency.plan())

    def test_amounts(self):
        self.assertTrue(all(1 <= a <= 1000 for g,i,a in concurrency.plan()))

    @patch.dict("os.environ", {"REALMPROOF_CONCURRENCY_DSN": ""})
    def test_requires_dedicated_dsn(self):
        with self.assertRaises(RuntimeError):
            concurrency.run()
