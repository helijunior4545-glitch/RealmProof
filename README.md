# RealmProof

**Intent-driven smart contract testing and verification for Gno.land**

> **Development status:** The Django studio and initial Gno realm are source-complete foundations, **not a verified live deployment or complete on-chain testing engine**. A Gno.land testnet deployment has not been confirmed. RealmProof is independent and unaffiliated with Gno.land.

## Why RealmProof?

Most blockchain tools start with an execution trace. RealmProof starts with the developer's intent: **What should this contract do, and what evidence would prove it?**

The studio organizes test scenarios into valid behavior, invalid inputs, access permissions, boundary conditions, state/repetition, integration, regression, properties and performance. Results distinguish *assertion verdict* from *execution status*.

## Features implemented

- English-first dark-console Django studio with a three-step intent-driven scenario builder, responsive workbench, and progressive evidence inspection.
- Organizational workspaces with membership-based access and project-scoped workflows.
- Scenarios with version-at-run snapshots of inputs and expected JSON.
- Deterministic, explicit-field assertion comparisons.
- Transparent evidence labeling: user-supplied evidence is **not** marked as on-chain verified.
- Immutable results after initial evaluation through studio endpoints.
- Audit records for workspace and execution actions.
- An independent Gno evidence registry under `realms/verification` that rejects duplicate digests.
- Initial Django tests, initial schema migration, GitHub Actions CI and Docker packaging.

## Quick start

Requirements: Python 3.12+, pip, and PostgreSQL for non-development environments.

```bash
git clone https://github.com/helijunior4545-glitch/RealmProof.git
cd RealmProof
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/accounts/login/.

To run the regression suite:

```bash
DJANGO_DEBUG=1 python manage.py test
DJANGO_DEBUG=1 python manage.py check
```

See [Console Workflow](docs/CONSOLE_WORKFLOW.md), [Getting Started](docs/GETTING_STARTED.md) and [Architecture](docs/ARCHITECTURE.md) for security boundaries, production configuration, and limitations.

## Gno component

`realms/verification/verification.gno` implements a hash registry with `RegisterEvidence`, `HasEvidence`, `Count` and `Render`. This anchors evidence commitments on-chain **once deployed**; it does not itself verify the correctness of a test or assert transaction provenance.

A successful Gno.land testnet deployment, chain metadata, and a reproducible demo are still required before this project can qualify for the Gnome Tavern hackathon.

## Roadmap

1. Verified Gno local test harness and on-chain testnet deployment.
2. Chain-aware read/call adapters with safe, wallet-approved signing.
3. Evidence ingestion with transaction hashes, block heights and verification.
4. Background execution workers, limits, and sandbox isolation.
5. Advanced test generation, scenario coverage and localization catalogs.

## License

MIT. This is an independent open-source project.
