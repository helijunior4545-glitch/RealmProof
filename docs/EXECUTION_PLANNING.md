# V6.1 execution preflight foundation

The internal prepare service rechecks current write membership and tenant scope, file SHA-256, proposal hash and bounded explicit assertions. It returns deterministic source-bound metadata and explicit blockers, never runs source, never enqueues a job and never claims a passing verdict. Expected digest fingerprints current intent, not an independently signed historical commitment. No browser endpoint, persistent plan, executable harness or sandbox is introduced. The next stage must implement isolated runtime and harness confirmation before dispatch.
