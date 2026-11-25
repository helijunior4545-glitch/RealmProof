# Analytical workspace visual refresh

## Reference

The UI is an original implementation informed by publicly documented Tenderly dashboard patterns, not a copy of the proprietary Tenderly web application. Product references:

- https://tenderly.co/blog/changelog/dashboard-redesign/
- https://tenderly.co/blog/changelog/transaction-overview-redesign/
- https://tenderly.co/developer-explorer

No Tenderly source code, brand assets or images were imported. Separate open-source Gno test discovery from Tenderly UI inspiration.

## Scope

Updated Network Explorer, Native Test Catalog, and Ledger Validation Lab templates; added a shared scoped stylesheet. Retained Django request handlers, routes, tenant authorization, and local Gno execution engine.

The layout provides persistent context tabs as real anchor links, searchable and paginated catalog tables, groups of assertion results, execution-evidence disclosure, explicit trust boundaries, and responsive two-column workbenches.

## Deliberate omissions

The interface does not claim state diffs, call traces, simulated fork execution, function-level gas profiling, or consensus proofs. No unimplemented feature is presented as operational. Reference snapshots must not be displayed as current query results.

## Acceptance checklist

1. Run `python manage.py check` and `python manage.py test`.
2. Visit Network Explorer with and without query parameters.
3. Verify Base64 and hex hashes, no-index block-height query, RPC failure.
4. Inspect the Native Test Catalog with GNOROOT configured and missing.
5. Test pagination and filters. Compare discovered counts with no pass claims.
6. Run the local ledger test on a host with Gno v1.8 CLI and GNOROOT.
7. Verify desktop, tablet and phone viewport, overflow, keyboard navigation.
