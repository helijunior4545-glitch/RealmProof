# Gnome Tavern submission

The DoraHacks event listing gives a deadline of **December 17, 2026 at 20:00 (UTC−5)** and explicitly requires a repository link and a demo video. Check the full Details tab before submission for track-specific rules and any further requirements.

| Item | Status |
| --- | --- |
| Repository | [RealmProof on GitHub](https://github.com/helijunior4545-glitch/RealmProof) |
| Demo video | Record and add to the submission |
| Guest demo | [Public Studio URL](https://p-a3001f8f92554e758bcdac87e2a093e5.lojasnova.com.br/studio/) · Recheck the guest journey and Gno runtime on the deployed version |
| Onyx registry | The submitter reported an accepted package upload at height 1438475. The last package metadata supplied by the submitter showed `inert`, pending approval. Activation and a public commitment lookup still need confirmation. |

## Record the demo

1. Open the landing in a fresh browser session and select **Open Project Studio**.
2. Run **Insufficient balance**. Show the rejection, all three matched assertions, and the Gno terminal output.
3. Run **Valid transfer** and open **Compare**. Contrast the recorded balances from the two executions.
4. In **Result**, download the individual **Evidence JSON** and compare `sha256sum <file>` with the report digest. **Export project evidence** is a separate project export and has different bytes.
5. If the registry is active and a write/read round trip has been confirmed, show the Onyx transaction and the public lookup for the same digest. See [Testnet evidence](TESTNET_EVIDENCE.md). Label local executions and testnet receipts separately.

For the guest rehearsal, follow [Local demo](LOCAL_DEMO.md). The Workbench runs bundled test scenarios through the Gno CLI. Its Onyx experiments verify the order and execution outcomes of previously submitted transactions through the public RPC.

## Recheck the submitted realm

```bash
rp_rpc=https://rpc.onyx.testnets.gno.land
rp_package=gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification
gnokey query vm/qpkgmeta_json -remote "$rp_rpc" -data "$rp_package"
gnokey query vm/qrender -remote "$rp_rpc" -data "$rp_package:"
```

The reported upload hash is `I0cNKq1eUE4s9WELIggAOmqnT2SQ1Yl+zuBryIC3O5Y=`. For a clean testnet demonstration, register a fresh run digest after activation and check it from a separate browser. Keep the transaction hash, block height, public URL and individual evidence JSON together.
