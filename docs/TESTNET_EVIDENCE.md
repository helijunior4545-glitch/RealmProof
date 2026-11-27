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

## Publish and register

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
