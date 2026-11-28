# RealmProof

**A testing and evidence workbench for Gno smart contracts.**

Define the behavior you expect, run a Gno scenario, and inspect the observations behind each verdict. Export the run as a JSON report and register its SHA-256 commitment on Gno.land.

[Onyx testnet deployment](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification) · [Hosted Studio](https://p-a3001f8f92554e758bcdac87e2a093e5.lojasnova.com.br/studio/) · [Hackathon submission guide](docs/HACKATHON_SUBMISSION.md)

## Try the hosted demo

1. Open the hosted Studio and select **Open Project Studio** to enter as a guest.
2. Run **Insufficient balance**. The default inputs request a transfer of `150` from a balance of `100`. The observed result is a rejection with the balance still at `100`.
3. Open **Compare** and select **Run transfer suite** to see expected and observed results for valid, insufficient-balance, and exact-balance transfers.
4. Open a scenario’s evidence. Select **Download JSON** to save the report, then select **Register on Onyx**. The hosted service submits the digest, so guests can use the flow without a wallet.
5. When the Workbench confirms the registration, select **Look up this hash on Onyx** and compare the public digest with the report SHA-256.

[Open the hosted Studio](https://p-a3001f8f92554e758bcdac87e2a093e5.lojasnova.com.br/studio/) · [Gnome Tavern submission guide](docs/HACKATHON_SUBMISSION.md)

## Verified on Onyx

A report generated in the hosted Workbench was registered on the Onyx testnet through the one-click flow. The public registry displays this SHA-256:

`e60c055bd2ed8693a4032534e6a02e95623e464d18969f68452c6714441f8281`

[Open the published report digest](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification:e60c055bd2ed8693a4032534e6a02e95623e464d18969f68452c6714441f8281)

To verify your own report, compute SHA-256 over the downloaded JSON file as-is and compare it with the registered digest. The transfer test runs off-chain. The realm stores the digest, and anyone can check the registration independently. [Evidence and operator setup guide](docs/TESTNET_EVIDENCE.md)

An earlier verification matched an exported report to the digest returned by `vm/qrender` at registration height `1451421`. Its transaction hash in Base64 is `tMPFYD44bZwWNVjTseyjhXySpPWT6P5cnTdfNjUwpjE=`. [Open the earlier digest](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification:2cafb80e0d13096b37eb3278f9c2607be7524fd3cdaca2c1191281459821ccfd)

## What you can do

| Workflow | What you see |
| --- | --- |
| Run a scenario | The transfer outcome, the expected and observed values, and a verdict for each assertion. |
| Inspect execution | Live output as the local Gno CLI emits it, recorded inputs, and fixture and harness source when their fingerprints match the run. |
| Compare runs | Differences in observed values across two recorded executions. |
| Export evidence | Individual Gno run reports with SHA-256 digests, plus a separate project-level JSON export. |
| Register evidence on Onyx | The hosted Workbench submits the report digest and opens the public registry after confirmation. |
| Inspect Onyx transactions | Compare the expected outcomes of previously submitted transactions with the RPC receipts, and verify their order by block height and transaction position. |

## Run locally

Use Python 3.12 or later, Node.js 22 with npm, and the Gno CLI. The project CI uses Gno v1.8.0. Put `gno` on your `PATH` and set `GNOROOT` to the corresponding Gno source checkout so the runner can load its standard libraries.

```bash
git clone https://github.com/helijunior4545-glitch/RealmProof.git
cd RealmProof

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

npm --prefix frontend install --no-package-lock --no-audit --no-fund
npm --prefix frontend run build

python manage.py setup_local_demo --settings=realmproof.settings_local
python manage.py runserver 127.0.0.1:8000 --settings=realmproof.settings_local
```

Open the [local Studio](http://127.0.0.1:8000/studio/). Local registration requires [signer configuration](docs/TESTNET_EVIDENCE.md).

## Execution and evidence

The transfer runner executes bundled Gno fixtures off-chain. Each run records the inputs, expectations, observed values, and source fingerprints used to interpret the result. The SHA-256 digest applies to the bytes of the individual evidence report.

The **Network** tab reads Onyx RPC data for transactions signed and submitted outside RealmProof. Actor labels are supplied by the user. The RPC results establish what the queried node reported. The separate Gno registry under `realms/verification/` records report digests and rejects duplicates. The registry renders publicly on Onyx.

## Project layout

| Path | Purpose |
| --- | --- |
| `studio/` | Django workspace, scenario runner, evidence reports, and network inspection |
| `frontend/` | React landing interactions and Test Workbench |
| `realms/` | Bundled Gno fixtures and the evidence registry |
| `docker/` | Container build definitions and runtime packaging |
| `docs/` | Architecture, deployment, and demonstration guides |

## Checks

```bash
python manage.py check --settings=realmproof.settings_local
REALMPROOF_ISOLATED_GUESTS=0 python manage.py test --settings=realmproof.settings_local
(cd realms/verification && gno test -v .)
```

[Architecture](docs/ARCHITECTURE.md) · [Deployment](docs/LOJASNOVA_DEPLOY.md) · [Onyx evidence guide](docs/TESTNET_EVIDENCE.md) · [Gnome Tavern submission](docs/HACKATHON_SUBMISSION.md)

## License

RealmProof is an independent project and is unaffiliated with Gno.land. [MIT License](LICENSE)
