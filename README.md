# RealmProof

**A testing and evidence workbench for Gno smart contracts.**

Define the behavior you expect, run a Gno scenario, and inspect the observations behind each verdict. Export the run as a JSON report and register its SHA-256 commitment on Gno.land.

[Onyx testnet deployment](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification) · [Hosted Studio](https://p-a3001f8f92554e758bcdac87e2a093e5.lojasnova.com.br/studio/) · [Hackathon submission guide](docs/HACKATHON_SUBMISSION.md)

## Verified on Onyx

On November 27, 2026, the SHA-256 of an exported Workbench report matched the digest registered on `onyx-1` and returned by a subsequent `vm/qrender` query.

| Field | Value |
| --- | --- |
| Report SHA-256 | `2cafb80e0d13096b37eb3278f9c2607be7524fd3cdaca2c1191281459821ccfd` |
| Registration height | `1451421` |
| Registration transaction hash (Base64) | `tMPFYD44bZwWNVjTseyjhXySpPWT6P5cnTdfNjUwpjE=` |

The registry lookup verifies that the digest was recorded. The report bytes are needed to recompute it. [Open the public digest lookup](https://onyx.testnets.gno.land/r/g16e6lg37nhkznu9vtzqka6amks6esgkaxe6x6vt/verification:2cafb80e0d13096b37eb3278f9c2607be7524fd3cdaca2c1191281459821ccfd) · [Reproduce the workflow](docs/TESTNET_EVIDENCE.md)

## Try the transfer lab

1. From the landing page, select **Open Project Studio** to enter as a guest.
2. Select **Insufficient balance** and click **Run scenario**. The default inputs ask to transfer `150` from a balance of `100`. Gno rejects the transfer, the balance remains `100`, and all three assertions match.
3. Open **Terminal → Output** for raw Gno output. In **Result**, use **Inspect evidence** to see the digest and **Download JSON** to save the individual report.
4. Run **Valid transfer** and open **Compare** to inspect how observed values differ between runs.

[Open the local Studio](http://127.0.0.1:8000/studio/)

## What you can do

| Workflow | What you see |
| --- | --- |
| Run a scenario | The transfer outcome, the expected and observed values, and a verdict for each assertion. |
| Inspect execution | Live output as the local Gno CLI emits it, recorded inputs, and fixture and harness source when their fingerprints match the run. |
| Compare runs | Differences in observed values across two recorded executions. |
| Export evidence | Individual Gno run reports with SHA-256 digests, plus a separate project-level JSON export. |
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
