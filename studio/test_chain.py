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
