# Verify a RealmProof commitment on Onyx

The Onyx testnet chain ID is `onyx-1` and the RPC is
`https://rpc.onyx.testnets.gno.land`. Use a funded testnet-only key in
`gnokey`. Request test tokens with the public address at the
[Onyx faucet](https://onyx.testnets.gno.land/faucet). Confirm the chain ID
and balance before signing.

## Prepare the report and the realm

1. Open the Studio, execute a bundled scenario in Gno, and open its report.
2. Download **Evidence JSON** and copy the displayed evidence digest. Compute
   SHA-256 over the downloaded file bytes to confirm the same digest. Do not
   reformat the JSON before hashing it.
3. Test the package locally from `realms/verification` with `gno test -v .`.

The generated JSON contains the run ID, inputs, expected and observed values,
verdict, and source and test harness fingerprints. The realm stores the digest
alone. Keep the JSON to independently reproduce the digest.

## Register from the Workbench

Create a dedicated key in a private keybase with the same `gnokey` version as
the server image, for example `gnokey add -home /path/to/onyx-keys realmproof-onyx`.
Fund its public address on Onyx and configure the RealmProof process:

| Environment variable | Value |
| --- | --- |
| `REALMPROOF_ONYX_KEY_HOME` | Absolute path to the dedicated keybase directory, writable by the app user |
| `REALMPROOF_ONYX_KEY_NAME` | Name of the testnet key in that directory |
| `REALMPROOF_ONYX_PASSWORD_FILE` | Absolute path to a private file containing the keybase password |

Mount the keybase and password file outside the repository with access limited to
the app user. Use a key dedicated to testnet and keep only demo funds in it. Both
runtime Dockerfiles include `gnokey`. The signer needs outbound HTTPS access to
the pinned Onyx RPC. Workers using the same signer must share the same keybase
directory for locking. Keep a single signer instance if the keybase cannot be
shared. The registry must already be deployed. The app submits only the report
digest and checks the registry before sending to avoid duplicate submissions.

Open an execution report and choose **Register on Onyx**. The operator's signer
pays the testnet fee. **Look up this hash on Onyx** appears after the public
registry confirms the hash. While confirmation is pending, use **Check
registration** to refresh the state. **Download JSON** is available throughout.

## Publish and register with gnokey

From the checkout, set `rp_address` and `rp_key` to the signer’s public address
and local key name. Set `rp_digest` to the 64-character digest copied from the
report. The packaged manifest uses the local development namespace. Make a copy
with your address-based namespace for the deploy.

```bash
rp_rpc=https://rpc.onyx.testnets.gno.land
rp_chain=onyx-1
rp_package="gno.land/r/$rp_address/verification"
rp_stage=$(mktemp -d)
cp realms/verification/verification.gno "$rp_stage/"
printf 'module = "%s"\ngno = "0.9"\n' "$rp_package" > "$rp_stage/gnomod.toml"

curl -fsS "$rp_rpc/status" | jq -e --arg chain "$rp_chain" '.result.node_info.network == $chain'
gnokey query "bank/balances/$rp_address" -remote "$rp_rpc"

gnokey maketx addpkg -pkgpath "$rp_package" -pkgdir "$rp_stage" \
  -gas-fee 5000ugnot -gas-wanted 5000000 \
  -chainid "$rp_chain" -remote "$rp_rpc" "$rp_key"

gnokey maketx call -pkgpath "$rp_package" -func RegisterEvidence -args "$rp_digest" \
  -gas-fee 3000ugnot -gas-wanted 3000000 \
  -chainid "$rp_chain" -remote "$rp_rpc" "$rp_key"

gnokey query vm/qrender -remote "$rp_rpc" -data "$rp_package:$rp_digest"
```

These limits cover the local rehearsal. Onyx may consume a different amount. Follow
simulation output and check the required storage deposit before broadcasting.
Save the deployment and registration transaction hashes from the receipts.
The read-only query should display `Registered evidence digest`.

Open `https://onyx.testnets.gno.land/r/<address>/verification:<digest>`
from a separate browser to confirm the public lookup. Include the deployed realm
link and a sample digest lookup in the submission. A successful lookup confirms
registration of the report digest. The report and its SHA-256 digest together
allow viewers to check which report was committed.

See the [Gno deployment guide](https://docs.gno.land/builders/getting-started)
and the [network list](https://docs.gno.land/resources/gnoland-networks).

## Onyx relay on an isolated Studio host

With the relay, the signer and read-only testnet queries use
`REALMPROOF_ONYX_RPC_RELAY`. They continue to validate the `onyx-1` chain ID.
Mainnet queries use their existing endpoint.

Run these steps on the Docker host. From a checkout of the app, identify the
RealmProof bridge and install the standalone relay on the host:

```bash
docker network inspect ln-studio-a3001f8f92554e758bcdac87e2a093e5 \
  --format '{{range .IPAM.Config}}{{println .Subnet .Gateway}}{{end}}'
install -m 0755 tools/onyx_rpc_relay.py /usr/local/bin/realmproof-onyx-relay
```

In `/etc/systemd/system/realmproof-onyx-relay.service`, use the IPv4 subnet
and gateway returned above. This example assumes `10.0.9.0/24` and
`10.0.9.1`. Confirm both values before starting.

```ini
[Unit]
Description=RealmProof private Onyx RPC relay
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
DynamicUser=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ExecStart=/usr/bin/python3 /usr/local/bin/realmproof-onyx-relay --bind 10.0.9.1 --allow-subnet 10.0.9.0/24
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now realmproof-onyx-relay.service
systemctl is-active realmproof-onyx-relay.service
```

The relay binds only to the project's bridge gateway, accepts only that
subnet, and sends permitted RPC requests to the fixed Onyx HTTPS endpoint with
TLS verification. It requires no keys or credentials. Traffic to the gateway
terminates on the host. If the host's INPUT firewall blocks it, permit TCP
8765 only on the RealmProof bridge, from its subnet to its gateway. Keep the
Studio forwarding restrictions in place.

In **RealmProof → Variáveis**, set `REALMPROOF_ONYX_RPC_RELAY` to
`http://10.0.9.1:8765` using the actual gateway, then publish. The existing
signer mounts and settings are required. If the Docker bridge gets a new
gateway or subnet, update both the service and the project variable.

From the published container, run:

```bash
python -c 'from studio.chain import status; print(status("testnet")["chain_id"])'
python -c 'from studio.chain import evidence_registered; print(evidence_registered("b2b264b82ad4c1c0dda548b332edb64fec540852fbd6ace6182db2b5b25df0e9"))'
```

Expect `onyx-1` and `True` respectively. Submit a new report through the public
Workbench and verify that the public Onyx lookup renders the same digest.
