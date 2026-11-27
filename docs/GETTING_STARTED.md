# Getting Started

RealmProof's interface and documentation use English as the source language.

## Local development

1. Create a Python 3.12 virtual environment.
2. Run `pip install -r requirements.txt`.
3. Run `cp .env.example .env` and export the variables, or set `DJANGO_DEBUG=1` for a local-only SQLite development database.
4. Run `python manage.py migrate`.
5. Run `python manage.py createsuperuser`.
6. Run `python manage.py runserver`.
7. Visit `http://127.0.0.1:8000/accounts/login/`.

A new user can create an organization, project, scenario, and test run. **Creating a run does not execute a blockchain transaction.** The present evaluation interface only compares user-supplied JSON with explicit assertions; it labels that evidence as unverified.

## Production deployment

Set a random `DJANGO_SECRET_KEY`, a PostgreSQL `DATABASE_URL`, `DJANGO_ALLOWED_HOSTS`, and HTTPS reverse proxy configuration. Run migrations before launching Gunicorn. The provided Docker Compose binds its web port to localhost intentionally; configure your reverse proxy and TLS separately.

For Docker Compose, set `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY` in your shell or a local untracked environment file and run `docker compose up --build -d`. Run `docker compose exec web python manage.py migrate` and `docker compose exec web python manage.py createsuperuser`.

## Gno realm

`realms/verification` contains an independently deployable evidence-hash registry written in Gno. It records digest commitments, **not the correctness of external evidence**. Install the official Gno tooling, then run `gno test -v .` from `realms/verification`. Follow the [testnet evidence guide](TESTNET_EVIDENCE.md) to download a report, publish the realm, and verify its digest. No deployment address is claimed here.

## Current limitations

This is a substantial *foundation*, not a finished on-chain testing service. Automated Gno transaction submission, signer integration, direct RPC trace ingestion, verified on-chain evidence, background processing, generated migrations, and live testnet deployment are not yet implemented. Do not submit it as a live hackathon build without implementing and verifying the missing on-chain work.
