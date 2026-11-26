# PM1 — Product maturity audit

Baseline: c17f3feec7558f01b70fcc06fc3c822c80d5280f. Static repository inspection; not a browser, accessibility conformance, live deployment or security certification.

## Inventory and proposed information architecture

| Surface | Existing entry points | Proposed home |
| --- | --- | --- |
| Public onboarding | guest entry, reference demo, login | Public / jury experience |
| Workspace | dashboard, organization, project creation | Workspace overview |
| Source | snapshot import, inventory, diff, structural/call/risk/recommendation/coverage inspection | Source Intelligence |
| Intent | scenario form, demo builder, source draft confirmation service | Test Studio |
| Execution | scenario execution, regression queue, universal engine and monitor, ledger lab, native catalog | Execution Center |
| Investigation | run detail, network explorer, risk indicators | Security and investigation |
| Evidence | JSON export, expiring review links, replay, revoke | Evidence and reports |
| Operations | health endpoint, Gno registry, local and production settings | Deployment and integration |

## Findings

- Shared navigation mixes platform, organization and tool scopes; universal engine lacked active-page semantics. Home redirects authenticated users to workspaces.
- Project workbench has useful intent/evidence separation and progressive disclosure; retain it. Its environment labels are static and should not imply runtime availability or evidence provenance for all runs.
- Source explorer stacks snapshots, inventory, structural declarations, call candidates, risk indicators and recommendations; use a file-centered layout with contextual inspection. Keep every existing capability and disclose parser limitations.
- Source draft confirmation and preflight are internal services, not browser workflows. Do not advertise imported-source execution.
- Universal engine is trusted fixture execution, not coverage of imported code. Preserve this distinction in all metrics.
- Run detail already separates assertion verdict and execution status. Preserve this contract.
- Guest entry is a dedicated one-click jury path; verify account isolation, quota behavior and deployed runtime before submission.
- Shared base hardcodes English and loads multiple CSS layers; consolidate tokens incrementally, audit responsive layouts, keyboard focus and contrast, then internationalize via Django catalogs.
- Source route fetches snapshot JSON for listing; defer large fields where safe and add route-level tenant, CSRF, escaping and quota tests.
- README feature inventory is behind the current implementation. Update with verified capabilities and explicit limitations during documentation phase.

## Delivery gates

P0: verify public deployment and Gno testnet registry availability, read/write evidence round trip, jury entry and actual runtime; keep credentials out of repository. No live deployment was checked in PM1.
P1 / PM2: inventory CSS tokens and components, establish keyboard and responsive acceptance checks.
P1 / PM3: unify project navigation and source-centered workspace; expose confirmed intent safely; preserve all existing routes and authorization.
P1 / PM4: separate staging and stable production, document worker/runtime dependencies and rollback.
P1 / PM5: rehearse jury workflow, document reproducible evidence and publish submission.
P2: resume V6.2+ isolated execution roadmap.

## PM1 changes

Low-risk shared-shell improvements: clarify Home label, group verification tools, expose current universal page and add keyboard skip link. No routes, models, permissions, execution engines or deployment settings changed. Browser validation remains pending. Existing visual language is retained.
