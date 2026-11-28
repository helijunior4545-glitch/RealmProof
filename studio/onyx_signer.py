"""Submit report commitments with the operator's dedicated Onyx keybase."""

import errno
import fcntl
import logging
import os
import shutil
import subprocess
from pathlib import Path
from time import time

from . import chain

logger = logging.getLogger(__name__)


class SignerError(RuntimeError):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def register(digest):
    home = os.environ.get("REALMPROOF_ONYX_KEY_HOME")
    key = os.environ.get("REALMPROOF_ONYX_KEY_NAME")
    password_file = os.environ.get("REALMPROOF_ONYX_PASSWORD_FILE")
    binary = shutil.which("gnokey")
    if not all((home, key, password_file, binary)) or key.startswith("-"):
        raise SignerError("Server registration is not configured. Ask the RealmProof operator to configure the Onyx testnet signer.")
    try:
        with Path(password_file).open("rb") as secret:
            password = secret.read(4097).rstrip(b"\r\n")
        if not password or len(password) > 4096 or b"\n" in password or b"\r" in password:
            raise SignerError("The server signer password file is invalid.")

        # Every worker using this keybase shares a lock and cooldown.
        with (Path(home) / ".realmproof-onyx.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if chain.evidence_registered(digest):
                return True
            lock.seek(0)
            last = float(lock.read() or 0)
            now = time()
            if now - last < 15:
                raise SignerError("The Onyx signer is cooling down. Try again in a few seconds.", 429)
            lock.seek(0)
            lock.truncate()
            lock.write(str(now))
            lock.flush()

            chain_id, rpc_url = chain.NETWORKS["testnet"]
            result = subprocess.run(
                [binary, "maketx", "call", "-home", home, "-insecure-password-stdin",
                 "-pkgpath", chain.ONYX_EVIDENCE_REALM, "-func", "RegisterEvidence",
                 "-args", digest, "-chainid", chain_id, "-remote", rpc_url,
                 "-gas-fee", "3000ugnot", "-gas-wanted", "3000000",
                 "-simulate", "test", "-broadcast=true", key],
                input=password + b"\n", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=15, check=False,
            )
            if result.returncode != 0:
                logger.warning("Onyx signer exited with status %s", result.returncode)
                raise SignerError("The Onyx signer could not submit the transaction. Ask the operator to check the testnet key, balance and RPC access.", 502)
    except subprocess.TimeoutExpired:
        # A broadcast may have reached the node after the connection timed out.
        return False
    except OSError as exc:
        if exc.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
            raise SignerError("The Onyx signer is processing another request. Try again shortly.", 429) from exc
        raise SignerError("The server could not access its Onyx signer.") from exc
    except ValueError as exc:
        raise SignerError("The server Onyx signer state is invalid.") from exc
    return False
