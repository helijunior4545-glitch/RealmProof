# Deploy RealmProof with LojasNova Programador

Use **Django + PostgreSQL**, the repository root, port 8000, health check
`/studio/health/`, and migrations enabled. The startup command is:

```sh
python manage.py collectstatic --noinput && gunicorn realmproof.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 2 --timeout 120
```

## Source image

The `LojasNova Studio source` workflow builds the React assets and publishes the
source archive at `ghcr.io/helijunior4545-glitch/realmproof-studio-source`. It
posts the `lojasnova/studio-source` status on the exact commit only after the
registry returns an image digest. The Programador GitHub App needs read access
to commit statuses, and the deployment host must be able to pull the image.
Connect the GHCR package to the repository and give the deployment host read
access if it is private.

## Runtime image

The source artifact relies on the operator-approved Django base. If that base
does not already have Gno v1.8.0 and the source parser, build the extension
below. Use the currently approved base pinned by digest and a destination
repository the deployment host is authorized to pull.

```sh
docker buildx build --platform linux/amd64 --push \
  --build-arg STUDIO_DJANGO_BASE="$APPROVED_DJANGO_BASE" \
  -f docker/Dockerfile.studio-runtime -t "$STUDIO_RUNTIME_TAG" .
```

Use the deployment host's architecture in place of `linux/amd64` if different.
Approve the resulting digest in the platform's
`PROGRAMADOR_RUNTIME_DJANGO_IMAGE` setting. This setting is platform-wide.
The extension preserves the approved base and adds Gno, its standard
libraries, and the RealmProof source parser.

## Verify the published visitor demo

Set `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and
`DJANGO_CSRF_TRUSTED_ORIGINS` for the public host. Keep `DJANGO_DEBUG=0`.
The database connection comes from the Programador.

For the isolated visitor flow, set `REALMPROOF_ISOLATED_GUESTS=1`,
`REALMPROOF_DEMO_USERNAME=hackathon_demo_public`, and the protected
`REALMPROOF_DEMO_PASSWORD`. Provision the dedicated reviewer account on the
published PostgreSQL database with `python manage.py create_reviewer
hackathon_demo_public`, using the same password.

In the published container, run `gno version` and
`python manage.py audit_engines transfer-v1`. In a private browser window,
open the landing, enter Project Studio, run **Insufficient balance**, and
download **Evidence JSON**. This checks the visitor configuration and runtime
beyond the HTTP health check.
