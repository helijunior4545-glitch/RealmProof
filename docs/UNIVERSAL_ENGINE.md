# Universal Test Engine V1
Fifteen intent categories; two trusted adapters with 35 planned checks. Existing Gno transfer and ledger fixtures are reused, not simulated. AuditEvent stores tenant-scoped execution results and evidence. No schema migration. POST requires write membership; GET requires membership. Infrastructure errors are inconclusive, not failed assertions. No arbitrary source, chain writes, or claims of full category coverage.

Limitations: synchronous execution (six transfer subprocesses may take up to 120 seconds), no durable job queue or quota, no OS sandbox, no full integration/security/fuzz/property/performance/mutation/concurrency adapter. Use trusted fixtures only. AuditEvent is not an immutable external proof. Run Django tests and real Gno suites before release.
