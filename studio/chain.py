"""Bounded read-only access to documented Gno RPC endpoints."""
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
    if network not in NETWORKS or method not in {"status", "tx"}:
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

def transaction(network, digest):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ChainError("Enter a 64-character hexadecimal transaction hash.")
    status(network)
    result = rpc(network, "tx", {"hash":"0x"+digest.upper()})
    if str(result.get("hash","")).removeprefix("0x").upper() != digest.upper():
        raise ChainError("Transaction identity mismatch.")
    return result
