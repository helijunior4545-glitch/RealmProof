# Architecture and Security Model

## Principles

- **Intent first:** each scenario records the purpose and expected outcome before execution.
- **Deterministic assertions:** pure evaluation logic does not depend on a language model.
- **Evidence provenance:** user-supplied observations must never masquerade as blockchain-verified results.
- **Tenant scoping:** project, scenario, run, and audit read/write paths filter by the authorized organization.
- **Role separation:** owner/admin/editor may write; viewer is read-only.
- **English-first:** identifiers, UI, documentation, and messages are authored in English.
- **Gno component:** a separate Gno realm anchors evidence digests without overclaiming their validity.

## Trust boundaries

Browser -> CSRF-protected Django views -> authenticated membership -> tenant-filtered database -> assertion evaluator. The Gno realm is a separate subsystem; there is no implemented bridge between the Django runs and the realm commitments yet.

Do not store private keys on the server. Require wallet-side approval for any future transaction signing flow. Treat all externally returned RPC text as untrusted, validate it before use, and preserve raw evidence with precise source metadata.

## Important gaps to close

1. Database-level tenant isolation and additional constraints for defense-in-depth.
2. Real Gno execution adapter, deterministic local harness and wallet integration.
3. Immutable evidence provenance with transaction hash, network, block height, confirmations and verification method.
4. Async job queue, retry policies, deduplication and concurrency control.
5. Accessibility, localization catalogs and browser-level end-to-end tests.
6. Verified Gno testnet deployment and demonstration.
