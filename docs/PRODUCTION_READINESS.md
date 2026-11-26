# PM6 — Production readiness, first gate

Public demo entry and launch responses are never cached. Guest sessions are explicitly marked. Shared demo membership is revalidated on tenant routes using membership_for; unexpected extra memberships, non-review tenants, elevated privileges or role changes fail closed. This does not provide per-visitor isolation, rate limiting or revocation of already published public review links. Dashboard and other routes not using membership_for require separate audit.

Source snapshot history defers the large files JSON column; selected and comparison snapshots still load their source as required.

Release gates remain: production image CI, browser acceptance, isolated visitor provisioning and bounded cleanup, public HTTPS smoke, Onyx registry read/write confirmation. No deployment, secrets, chain writes or hosting changes performed. Do not publish private source in the shared demo.
