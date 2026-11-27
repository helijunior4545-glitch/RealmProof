import base64
from unittest.mock import patch

from django.test import SimpleTestCase

from . import chain, network_experiments


class NetworkExperimentTests(SimpleTestCase):
    def step(self, digit, expected="passed"):
        return {"name": "Operation", "actor": "Operator", "hash": digit * 64, "height": 42, "expected": expected}

    @patch("studio.network_experiments.chain.transaction")
    def test_expected_failure_and_order_within_a_block(self, transaction):
        steps = [self.step("a"), self.step("b", "failed")]
        transaction.side_effect = [
            {"height": 42, "index": 0, "execution": "passed"},
            {"height": 42, "index": 3, "execution": "failed"},
        ]
        report = network_experiments.evaluate(network_experiments.validate_steps(steps))
        self.assertEqual(report["verdict"], "passed")
        self.assertEqual(report["steps"][1]["actor_verification"], "declared")
        transaction.assert_called_with("testnet", "b" * 64, 42)

    @patch("studio.network_experiments.chain.transaction")
    def test_out_of_order_evidence_fails_and_unavailable_is_inconclusive(self, transaction):
        transaction.side_effect = [
            {"height": 42, "index": 3, "execution": "passed"},
            chain.ChainError("Unavailable"),
            {"height": 42, "index": 0, "execution": "passed"},
        ]
        report = network_experiments.evaluate([self.step("a"), self.step("b"), self.step("c")])
        self.assertEqual(report["verdict"], "failed")
        self.assertEqual([step["verdict"] for step in report["steps"]], ["passed", "inconclusive", "failed"])

    def test_duplicate_hashes_are_rejected_across_encodings(self):
        first = self.step("a")
        second = {**first, "hash": base64.b64encode(bytes.fromhex(first["hash"])).decode()}
        with self.assertRaisesMessage(ValueError, "reuses a transaction"):
            network_experiments.validate_steps([first, second])
