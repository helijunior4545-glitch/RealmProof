"""Bounded read-only access to documented Gno RPC endpoints."""
import base64
import binascii
import hashlib
import json
import re
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import URLError
from urllib.parse import urlencode

NETWORKS = {
    "testnet": ("onyx-1", "https://rpc.onyx.testnets.gno.land"),
    "mainnet": ("gnoland-1", "https://rpc.gno.land"),
}

class ChainError(RuntimeError):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def rpc(network, method, params=None):
    if network not in NETWORKS or method not in {"status", "tx", "block", "block_results", "abci_query"}:
        raise ChainError("Unsupported network or method.")
    url = NETWORKS[network][1] + "/" + method
    if params:
        url += "?" + urlencode(params)
    try:
        with build_opener(NoRedirect()).open(Request(url, headers={"Accept":"application/json"}), timeout=5) as response:
            raw = response.read(1048577)
        if len(raw) > 1048576:
            raise ChainError("RPC response exceeds limit.")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or payload.get("error") or not isinstance(payload.get("result"), dict):
            raise ChainError("RPC rejected the query.")
        return payload["result"]
    except (URLError, OSError, ValueError) as exc:
        raise ChainError("Network response unavailable or invalid.") from exc

def status(network):
    result = rpc(network, "status")
    try:
        chain = result["node_info"]["network"]
        sync = result["sync_info"]
        height = int(sync["latest_block_height"])
        catching_up = sync["catching_up"]
        if chain != NETWORKS[network][0] or height < 1 or type(catching_up) is not bool:
            raise ChainError("Network identity or status mismatch.")
        return {"chain_id":chain,"height":height,"catching_up":catching_up,"block_time":sync["latest_block_time"]}
    except (KeyError, ValueError, TypeError) as exc:
        raise ChainError("Unexpected status response.") from exc

def normalize_hash(value):
    if re.fullmatch(r"(?:0x)?[0-9a-fA-F]{64}", value):
        return bytes.fromhex(value.removeprefix("0x"))
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) == 32:
            return raw
    except (ValueError, binascii.Error):
        pass
    raise ChainError("Enter a SHA-256 transaction hash in hexadecimal or Base64.")

def transaction(network, digest, height=None):
    target = normalize_hash(digest)
    if height is None:
        status(network)
        result = rpc(network, "tx", {"hash": "0x" + target.hex().upper()})
        if normalize_hash(str(result.get("hash", ""))) != target:
            raise ChainError("Transaction identity mismatch.")
        return result
    if not re.fullmatch(r"[1-9][0-9]{0,17}", str(height)):
        raise ChainError("Enter a positive block height.")
    node = status(network)
    if node["catching_up"] or int(height) > node["height"]:
        raise ChainError("Block is not available on the synchronized node.")
    params = {"height": str(height)}
    block = rpc(network, "block", params)
    receipts = rpc(network, "block_results", params)
    try:
        header = block["block"]["header"]
        if header["chain_id"] != node["chain_id"] or int(header["height"]) != int(height) or int(receipts["height"]) != int(height):
            raise ChainError("Block identity mismatch.")
        txs = block["block"]["data"]["txs"] or []
        results = receipts["results"]["deliver_tx"] or []
        if not isinstance(txs, list) or not isinstance(results, list) or len(txs) != len(results):
            raise ChainError("Transaction and receipt counts differ.")
        matches = []
        for index, encoded in enumerate(txs):
            raw = base64.b64decode(encoded, validate=True)
            if hashlib.sha256(raw).digest() == target:
                matches.append((index, len(raw)))
        if len(matches) != 1:
            raise ChainError("Transaction not uniquely matched in block.")
        index, size = matches[0]
        receipt = results[index]
        response = receipt["ResponseBase"]
        error = response["Error"]
        log = response.get("Log", "")
        verdict = "failed" if error is not None or "success:false" in log else "passed" if "success:true" in log else "unknown"
        return {"chain_id": node["chain_id"], "height": int(height), "index": index,
                "hash_hex": target.hex(), "hash_base64": base64.b64encode(target).decode(),
                "size_bytes": size, "inclusion": "matched_rpc_block",
                "execution": verdict, "package_availability": "unverified",
                "receipt": receipt, "trust": "RPC-reported block and receipt; not a consensus proof"}
    except (KeyError, TypeError, ValueError, AttributeError, binascii.Error) as exc:
        raise ChainError("Unexpected block or receipt response.") from exc


ONYX_EVIDENCE_REALM = "gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification"


def evidence_registered(digest):
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ChainError("Invalid evidence digest.")
    if status("testnet")["catching_up"]:
        raise ChainError("Onyx node is synchronizing.")
    result = rpc("testnet", "abci_query", {
        "path": '"vm/qrender"',
        "data": json.dumps(base64.b64encode(f"{ONYX_EVIDENCE_REALM}:{digest}".encode()).decode()),
    })
    try:
        response = result["response"]["ResponseBase"]
        if response["Error"] is not None:
            raise ChainError("Onyx rejected the evidence lookup.")
        rendered = base64.b64decode(response["Data"], validate=True).decode()
    except (KeyError, TypeError, ValueError) as exc:
        raise ChainError("Unexpected evidence lookup response.") from exc
    if f"Registered evidence digest: `{digest}`" in rendered.splitlines():
        return True
    if "Evidence digest not found." in rendered.splitlines():
        return False
    raise ChainError("Unexpected evidence registry content.")
