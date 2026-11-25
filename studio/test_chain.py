from unittest.mock import patch
from django.test import SimpleTestCase
from . import chain

class ChainTests(SimpleTestCase):
    @patch("studio.chain.rpc")
    def test_status(self, rpc):
        rpc.return_value = {"node_info":{"network":"onyx-1"},"sync_info":{"latest_block_height":"42","catching_up":False,"latest_block_time":"2026-11-25T00:00:00Z"}}
        self.assertEqual(chain.status("testnet")["height"],42)
        with self.assertRaises(chain.ChainError):
            chain.status("mainnet")

    def test_invalid_hash(self):
        with self.assertRaises(chain.ChainError):
            chain.transaction("testnet","bad")

    def test_unknown_network(self):
        with self.assertRaises(chain.ChainError):
            chain.rpc("custom","status")

    @patch("studio.chain.status")
    @patch("studio.chain.rpc")
    def test_wrong_transaction(self,rpc,status):
        rpc.return_value={"hash":"B"*64}
        with self.assertRaises(chain.ChainError):
            chain.transaction("testnet","A"*64)

    @patch("studio.chain.status")
    @patch("studio.chain.rpc")
    def test_block_receipt_without_index(self, rpc, status):
        import hashlib
        import base64
        raw = b"test transaction"
        digest = base64.b64encode(hashlib.sha256(raw).digest()).decode()
        status.return_value = {"chain_id": "onyx-1", "height": 42, "catching_up": False}
        block = {"block": {"header": {"chain_id": "onyx-1", "height": "42"},
                           "data": {"txs": [base64.b64encode(raw).decode()]}}}
        receipt = {"ResponseBase": {"Error": None, "Log": "msg:0,success:true,log:,events:[]"}}
        results = {"height": "42", "results": {"deliver_tx": [receipt]}}
        rpc.side_effect = [block, results]
        result = chain.transaction("testnet", digest, "42")
        self.assertEqual(result["execution"], "passed")
        self.assertEqual(result["package_availability"], "unverified")
        self.assertEqual(result["index"], 0)
        receipt["ResponseBase"]["Error"] = {"message": "failed"}
        rpc.side_effect = [block, results]
        self.assertEqual(chain.transaction("testnet", digest, "42")["execution"], "failed")
        rpc.side_effect = [block, results]
        with self.assertRaises(chain.ChainError):
            chain.transaction("testnet", "a"*64, "42")
