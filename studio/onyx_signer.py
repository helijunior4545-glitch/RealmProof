"""Submit report commitments with the operator's dedicated Onyx keybase."""

import errno
import fcntl
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from time import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from . import chain

logger = logging.getLogger(__name__)


class SignerError(RuntimeError):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


TOKEN_PATTERN = r"[0-9a-f]{64}"
DIGEST_PATTERN = r"[0-9a-f]{64}"
SIGNER_PATH = "/realmproof/register"


def register(digest):
    if not re.fullmatch(DIGEST_PATTERN, digest):
        raise SignerError("Invalid evidence digest.", 400)
    token = os.environ.get("REALMPROOF_ONYX_SIGNER_TOKEN")
    if token is None:
        return register_local(digest)
    if not re.fullmatch(TOKEN_PATTERN, token) or not os.environ.get("REALMPROOF_ONYX_RPC_RELAY", "").strip():
        raise SignerError("The private Onyx signer is not configured correctly.")
    request = Request(
        chain.rpc_endpoint("testnet") + SIGNER_PATH,
        data=json.dumps({"digest": digest}).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with build_opener(chain.NoRedirect(), ProxyHandler({})).open(request, timeout=30) as response:
            payload = json.loads(response.read(2049))
            if not isinstance(payload, dict) or type(payload.get("registered")) is not bool:
                raise ValueError
            if (response.status, payload["registered"]) not in {(200, True), (202, False)}:
                raise ValueError
            return payload["registered"]
    except HTTPError as exc:
        if exc.code == 429:
            raise SignerError("The private Onyx signer is busy. Try again shortly.", 429) from exc
        if exc.code in (401, 403):
            raise SignerError("The private Onyx signer rejected authentication.") from exc
        raise SignerError("The private Onyx signer could not register the evidence.") from exc
    except TimeoutError:
        return False  # The host may have submitted before the timeout.
    except (URLError, OSError, ValueError) as exc:
        raise SignerError("The private Onyx signer is unavailable.") from exc


def register_local(digest):
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

            chain_id = chain.NETWORKS["testnet"][0]
            rpc_url = chain.rpc_endpoint("testnet")
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
