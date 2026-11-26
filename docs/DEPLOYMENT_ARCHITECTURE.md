# PM4 — Deployment architecture

## Environments
Development: local settings and isolated SQLite. Staging: separate PostgreSQL database, secrets, host and worker. Production: reviewed immutable commit/image, separate PostgreSQL and secrets. Jury: dedicated review workspace; currently shared mutable account, not per-visitor isolation. Onyx: independent Gno registry; availability and write/read round trip remain release blockers.

## Build and release
Build from repository root: docker build -f docker/Dockerfile -t realmproof:<commit> .
The image includes pinned Gno v1.8.0 source/runtime and static parser. Build is not yet verified by CI. Run migrations as a single release task, not in each web replica. Start web using image default command; run separate worker with python manage.py process_universal --watch. Configure any additional regression worker according to existing commands. Never expose PostgreSQL publicly. Use separate database backups and restore rehearsal. Keep previous image and check migration compatibility before rollback.

Required runtime secrets: DJANGO_SECRET_KEY, DATABASE_URL, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS; DJANGO_DEBUG=0. Use TLS termination at trusted ingress, secure cookies, and restrict direct backend access. Do not assume forwarded headers are trusted. Jury credentials must be runtime secrets. Do not share production database with staging. Concurrency audit DSN must point to a dedicated disposable database, never production.

## Release gates
1. CI green for exact commit; image build and runtime smoke checks.
2. Migration, static manifest, health endpoint, login and guest launch over HTTPS.
3. Separate worker processes a trusted job; verify actual results and source parser.
4. Onyx RPC chain identity, realm availability and independent evidence write/read; registry stores digests, not proof of test correctness.
5. Verify jury isolation, quotas, reset policy and public demo; no production customer data.
6. Browser checks for PM1–PM3, then publish stable URL and demo documentation.

No hosting resources, DNS, secrets, deployment or chain transactions were changed in PM4. Existing deployment may use a different build mechanism; explicitly select the Dockerfile when provisioning. Image size and resource needs require measurement. 
