from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase
from . import mutation
from .universal import execute

class MutationTests(SimpleTestCase):
    def test_unique_mutants(self):
        source = (Path(__file__).resolve().parent.parent / "realms/ledger/ledger.gno").read_text()
        variants = list(mutation.mutants(source))
        self.assertEqual(len(variants), 32)
        self.assertEqual(len({v[1] for v in variants}), 32)
        self.assertTrue(all(v[1] != source for v in variants))

    def test_probes(self):
        self.assertEqual(len(mutation.probes()), 96)

    @patch("studio.mutation.shutil.which", return_value="gno")
    @patch("studio.mutation.observe")
    def test_survivors_are_not_kills(self, observe, binary):
        observe.return_value = [True]*96
        result = execute("mutation-v1")
        self.assertEqual(result["verdict"], "failed")
        self.assertEqual(len(result["rows"]), 32)

    @patch("studio.mutation.shutil.which", return_value="gno")
    @patch("studio.mutation.observe", side_effect=RuntimeError("build error"))
    def test_runtime_error_is_inconclusive(self, observe, binary):
        result = execute("mutation-v1")
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["rows"], [])
