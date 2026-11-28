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

## Private host signer for Studio projects without volumes

The Studio rejects persistent mounts on managed applications. Run signing on the
host alongside the relay for those applications. Preserve the existing
`/srv/realmproof/onyx-keys` and `/srv/realmproof/onyx-password` files when removing
the two mounts from Coolify. The key must be funded on `onyx-1`.

On the host, from a checkout containing this version, install the service code:

```bash
install -d -m 0755 /opt/realmproof-onyx/tools /opt/realmproof-onyx/studio
install -m 0644 tools/onyx_rpc_relay.py /opt/realmproof-onyx/tools/
install -m 0644 studio/{__init__,chain,onyx_signer}.py /opt/realmproof-onyx/studio/
```

Install the pinned `gnokey` v1.8.0 binary on the host. It can be copied from
the already approved RealmProof runtime container with
`docker cp CONTAINER_ID:/usr/local/bin/gnokey /usr/local/bin/gnokey`. Confirm
the binary runs on the host. Use the same dedicated UID/GID as the existing
key files (10001 in this example). The parent directory must be traversable:
`chgrp 10001 /srv/realmproof && chmod 0710 /srv/realmproof`. Keep the key
directory private and writable by UID 10001, and the password file private and
readable by UID 10001.

Create a separate authentication token, keeping the host copy readable only
by root. Run once:

```bash
(umask 077; set -o noclobber; openssl rand -hex 32 > /srv/realmproof/onyx-signer-token)
```

Replace the relay service's existing `[Service]` section with the following.
Retain its existing `[Unit]` and `[Install]` sections. Use the actual project
bridge gateway and subnet. This service occupies the original relay port.

```ini
[Service]
Type=simple
User=10001
Group=10001
WorkingDirectory=/opt/realmproof-onyx
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/srv/realmproof/onyx-keys
LoadCredential=onyx-signer-token:/srv/realmproof/onyx-signer-token
Environment=REALMPROOF_ONYX_KEY_HOME=/srv/realmproof/onyx-keys
Environment=REALMPROOF_ONYX_KEY_NAME=realmproof-onyx
Environment=REALMPROOF_ONYX_PASSWORD_FILE=/srv/realmproof/onyx-password
ExecStart=/usr/bin/python3 -m tools.onyx_rpc_relay --bind 10.0.9.1 --allow-subnet 10.0.9.0/24 --signer-token-file %d/onyx-signer-token
Restart=on-failure
RestartSec=5
```

Run `systemctl daemon-reload` and
`systemctl enable --now realmproof-onyx-relay.service`, then restart it if
it was already running. In the RealmProof project's protected runtime
variables, set `REALMPROOF_ONYX_RPC_RELAY` to its confirmed bridge gateway URL
and `REALMPROOF_ONYX_SIGNER_TOKEN` to the token generated above. The three
keybase-related variables belong on the host service in this mode and may be
removed from the app. Resolve the previous operation in the Studio once the
mounts are gone, then publish a fresh version.

The app sends only the report digest on the isolated bridge. The token
authenticates that request, and the host signer chooses the fixed realm,
function, and fee. Raw broadcast RPC is disabled on this relay in signer
mode. Public confirmation remains a separate read from the live registry.
Keep the relay private to the RealmProof bridge and avoid exposing port 8765
through the public reverse proxy.

### Persist the RealmProof bridge exception on zion2test

Once the relay works, run `bash tools/install_onyx_relay_firewall.sh` as root
on zion2test. This installer is scoped to the current RealmProof bridge,
`10.0.9.0/24`, and its private relay at `10.0.9.1:8765`. It validates the
Docker network before installing an INPUT rule and reconciles that rule via
systemd after boot and after firewall reloads. The Studio-managed chains
remain untouched. If the gateway or subnet changes, update the installer,
the relay service and the project's relay URL together.

Verify with:

```bash
systemctl is-active realmproof-onyx-firewall.timer
iptables -w -S INPUT 1
```

The timer should be active and the first INPUT rule should carry the
`realmproof-onyx-relay` comment. From the RealmProof container, check
`studio.chain.status("testnet")` before testing a new registration.
