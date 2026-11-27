# Gnome Tavern submission

The Gnome Tavern rules require a **working Gno.land testnet deployment at the time of submission** and a link to that deployment. Submissions close **December 18, 2026 at 01:00 UTC** (December 17 at 20:00 UTC−5).

| Requirement | RealmProof |
| --- | --- |
| Working testnet deployment and link | The public page returned HTTP 200 and displayed *RealmProof Evidence Registry* on November 27, 2026. [Onyx deployment](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification) |
| Public code | [RealmProof on GitHub](https://github.com/helijunior4545-glitch/RealmProof) |
| Genuine Gno component | [Evidence registry source](../realms/verification/verification.gno) |
| README | [Project overview and local setup](../README.md) |
| Demo video | Recorded by the submitter. Confirm judging access and attach the video link. |
| Short project description | Use or adapt the description below. |

**Short description:** RealmProof is a testing and evidence workbench for Gno smart contracts. Developers run scenarios, compare expected and observed behavior, inspect execution output, and export reproducible reports. A Gno realm records SHA-256 commitments for those reports.

The [hosted Studio](https://p-a3001f8f92554e758bcdac87e2a093e5.lojasnova.com.br/studio/) is a supporting demo link. Supply the working Gno.land testnet realm link as the deployment link.

## Record the demo

1. Open the landing in a fresh browser session and select **Open Project Studio**.
2. Run **Insufficient balance**. Show the rejection, all three matched assertions, and the Gno terminal output.
3. Run **Valid transfer** and open **Compare**. Contrast the recorded balances from the two executions.
4. In **Result**, download the individual **Evidence JSON** and compare `sha256sum <file>` with the report digest. **Export project evidence** is a separate project export and has different bytes.
5. Show the Onyx registration and the public digest lookup from the verified example in the README. See [Testnet evidence](TESTNET_EVIDENCE.md). Label local executions and testnet receipts separately.

For the guest rehearsal, follow [Local demo](LOCAL_DEMO.md). The Workbench runs bundled test scenarios through the Gno CLI. Its Onyx experiments verify the order and execution outcomes of previously submitted transactions through the public RPC.

## Recheck the submitted realm

```bash
rp_rpc=https://rpc.onyx.testnets.gno.land
rp_package=gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification
gnokey query vm/qpkgmeta_json -remote "$rp_rpc" -data "$rp_package"
gnokey query vm/qrender -remote "$rp_rpc" -data "$rp_package:"
```

The reported upload hash is `I0cNKq1eUE4s9WELIggAOmqnT2SQ1Yl+zuBryIC3O5Y=`. For a clean testnet demonstration, register a fresh run digest after activation and check it from a separate browser. Keep the transaction hash, block height, public URL and individual evidence JSON together.

The reported registration transaction was included at height `1451421` with hash `tMPFYD44bZwWNVjTseyjhXySpPWT6P5cnTdfNjUwpjE=`. The Onyx query returned the same digest that was computed from the downloaded report. [Public digest lookup](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification:2cafb80e0d13096b37eb3278f9c2607be7524fd3cdaca2c1191281459821ccfd)
