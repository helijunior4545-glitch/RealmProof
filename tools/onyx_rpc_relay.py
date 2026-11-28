#!/usr/bin/env python3
"""Private HTTP relay to the fixed Onyx JSON-RPC endpoint."""

import argparse
import hmac
import ipaddress
import json
import os
import re
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import BoundedSemaphore
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

UPSTREAM = "https://rpc.onyx.testnets.gno.land"
METHODS = frozenset({
    "status", "tx", "block", "block_results", "abci_query",
    "consensus_params", "broadcast_tx_commit",
})
REQUEST_LIMIT = 65536
RESPONSE_LIMIT = 4194304
WRITABLE_METHODS = {"broadcast_tx_commit"}
SIGNER_PATH = "/realmproof/register"
PRIVATE_NETWORKS = tuple(ipaddress.IPv4Network(value) for value in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class Relay(ThreadingHTTPServer):
    request_queue_size = 16
    daemon_threads = True

    def __init__(self, address, source_network, signer_token=None):
        self.source_network = source_network
        self.signer_token = signer_token
        self.methods = METHODS - WRITABLE_METHODS if signer_token else METHODS
        self.slots = BoundedSemaphore(8)
        super().__init__(address, Handler)

    def verify_request(self, request, address):
        return ipaddress.IPv4Address(address[0]) in self.source_network

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    timeout = 5

    def log_message(self, *args):
        # RPC query strings may contain signed transaction bytes.
        pass

    def do_GET(self):
        path = urlsplit(self.path)
        if path.scheme or path.netloc or path.fragment or path.path[1:] not in self.server.methods:
            self.send_error(404)
            return
        self.forward(path.path + ("?" + path.query if path.query else ""))

    def do_POST(self):
        if self.server.signer_token and self.path == SIGNER_PATH:
            self.register_evidence()
            return
        if self.path != "/":
            self.send_error(404)
            return
        try:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length") or []) != 1:
                raise ValueError
            length = int(self.headers["Content-Length"])
            if not 0 < length <= REQUEST_LIMIT:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get("method"), str) or payload["method"] not in self.server.methods:
                raise ValueError
        except (ValueError, TimeoutError):
            self.send_error(400)
            return
        self.forward("/", json.dumps(payload).encode())

    def register_evidence(self):
        from studio import chain, onyx_signer

        authorization = self.headers.get("Authorization", "").encode("latin-1")
        expected = ("Bearer " + self.server.signer_token).encode()
        if not hmac.compare_digest(authorization, expected):
            self.send_error(401)
            return
        try:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length") or []) != 1:
                raise ValueError
            length = int(self.headers["Content-Length"])
            if not 0 < length <= 256:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            if (
                not isinstance(payload, dict) or set(payload) != {"digest"}
                or not isinstance(payload["digest"], str)
                or not re.fullmatch(onyx_signer.DIGEST_PATTERN, payload["digest"])
            ):
                raise ValueError
        except (ValueError, TimeoutError):
            self.send_error(400)
            return
        try:
            registered = onyx_signer.register_local(payload["digest"])
        except onyx_signer.SignerError as exc:
            self.send_error(exc.status)
            return
        except chain.ChainError:
            self.send_error(502)
            return
        self.send_json(200 if registered else 202, json.dumps({"registered": registered}).encode())

    def forward(self, path, body=None):
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(UPSTREAM + path, data=body, headers=headers)
        try:
            with build_opener(NoRedirect(), ProxyHandler({})).open(request, timeout=10) as upstream:
                response = upstream.read(RESPONSE_LIMIT + 1)
            if len(response) > RESPONSE_LIMIT:
                raise ValueError
        except (URLError, OSError, ValueError):
            self.send_error(502, "Onyx upstream unavailable")
            return
        self.send_json(200, response)

    def send_json(self, status, response):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        try:
            self.wfile.write(response)
        except (OSError, socket.timeout):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", required=True, type=ipaddress.IPv4Address)
    parser.add_argument("--allow-subnet", required=True, type=ipaddress.IPv4Network)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--signer-token-file", type=Path)
    args = parser.parse_args()
    if args.bind not in args.allow_subnet or not any(
        args.allow_subnet.subnet_of(network) for network in PRIVATE_NETWORKS
    ) or not 1024 <= args.port <= 65535:
        parser.error("bind must belong to the allowed private subnet and port must be 1024–65535")
    token = None
    if args.signer_token_file:
        if os.getenv("REALMPROOF_ONYX_RPC_RELAY"):
            parser.error("the host signer must use the official Onyx endpoint directly")
        try:
            with args.signer_token_file.open() as file:
                token = file.read(128).strip()
        except (OSError, ValueError):
            parser.error("signer token file is unreadable")
        if not re.fullmatch(r"[0-9a-f]{64}", token):
            parser.error("signer token must be a 64-character lowercase hexadecimal value")
    with Relay((str(args.bind), args.port), args.allow_subnet, token) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
