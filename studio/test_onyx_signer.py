from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from . import onyx_signer


class OnyxSignerTests(SimpleTestCase):
    @patch("studio.onyx_signer.subprocess.run")
    @patch("studio.onyx_signer.chain.evidence_registered")
    @patch("studio.onyx_signer.shutil.which", return_value="/usr/bin/gnokey")
    def test_existing_hash_skips_signing_and_new_hash_uses_pinned_testnet(self, which, lookup, execute):
        digest = "a" * 64
        with TemporaryDirectory() as home:
            password = Path(home) / "secret"
            password.write_bytes(b"test-password\n")
            with patch.dict("os.environ", {
                "REALMPROOF_ONYX_KEY_HOME": home,
                "REALMPROOF_ONYX_KEY_NAME": "signer",
                "REALMPROOF_ONYX_PASSWORD_FILE": str(password),
            }):
                lookup.return_value = True
                self.assertTrue(onyx_signer.register(digest))
                execute.assert_not_called()

                lookup.return_value = False
                execute.return_value.returncode = 0
                self.assertFalse(onyx_signer.register(digest))
                command = execute.call_args.args[0]
                self.assertEqual(command[command.index("-args") + 1], digest)
                self.assertEqual(command[command.index("-chainid") + 1], "onyx-1")
                self.assertEqual(execute.call_args.kwargs["input"], b"test-password\n")
                self.assertNotIn("test-password", command)
                with self.assertRaises(onyx_signer.SignerError) as error:
                    onyx_signer.register("b" * 64)
                self.assertEqual(error.exception.status, 429)
                execute.assert_called_once()
