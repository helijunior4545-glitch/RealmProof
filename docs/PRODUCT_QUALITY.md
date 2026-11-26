# PM5 — Jury experience and continuous product quality

The landing page describes a reproducible trusted-fixture journey and warns that the demo account is shared. No per-visitor isolation, private-source safety or testnet availability is claimed. Monitor refresh has bounded request timeout, manual activity feedback, overlap prevention and preserves existing results on failure. Expanded details and focused controls prevent replacement. Manual refresh works while paused. Browser validation remains required.

Every new UI feature must preserve native validation, keyboard focus, reduced motion, responsive layout, textual states, meaningful pending/error/empty feedback and evidence provenance. Do not simulate progress or imply success before confirmation. Avoid automatic mutation retries. Test tenant authorization and server-side idempotency separately.

CI now includes a separate production-image build and smoke job: non-root runtime, parser, PostgreSQL migrations, trusted transfer suite and HTTP health. This is not a deployment or full production certification. Release blockers remain actual Onyx registry round trip, public HTTPS guest journey, visitor isolation and browser checks.
